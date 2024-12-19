import contextlib
import json
import logging
import typing
import urllib.parse

import chalice.constants
import firebase_admin
import firebase_admin.credentials
import httpx
import pydantic
import pydantic_settings

AllowedToastServices = typing.Literal["alimtalk"]
logger = logging.getLogger(__name__)


def log_request(req: httpx.Request) -> None:
    logger.info(f"REQ [{req.method}]{req.url}")


def log_response(resp: httpx.Response) -> None:
    req = resp.request
    logger.info(f"RES [{req.method}]{req.url}<{resp.status_code}> {resp.read().decode(errors='ignore')=}")


class ChaliceAPIGatewayCustomDomainConfig(pydantic.BaseModel):
    domain_name: str
    certificate_arn: str
    tls_version: typing.Literal["TLS_1_0", "TLS_1_2"] = chalice.constants.DEFAULT_TLS_VERSION  # TLS_1_2
    url_prefix: str | None = None
    tags: dict[str, str] | None = None


class ChaliceLambdaConfig(pydantic.BaseModel):
    autogen_policy: bool = True
    iam_policy_file: pydantic.FilePath | None = None
    iam_role_arn: str | None = None
    manage_iam_role: bool = True
    subnet_ids: list[str] | None = None
    security_group_ids: list[str] | None = None

    lambda_memory_size: int | None = chalice.constants.DEFAULT_LAMBDA_MEMORY_SIZE
    lambda_timeout: int | None = chalice.constants.DEFAULT_LAMBDA_TIMEOUT
    layers: list[str] | None = None
    log_retention_in_days: int | None = None
    reserved_concurrency: int | None = None

    environment_variables: dict[str, str] | None = None
    tags: dict[str, str] | None = None

    @pydantic.field_validator("lambda_memory_size", mode="before")
    @classmethod
    def validate_lambda_memory_size(cls, lambda_memory_size: int) -> int:
        if lambda_memory_size % 64 != 0:
            raise ValueError("lambda_memory_size must be a multiple of 64")

        return lambda_memory_size

    @pydantic.model_validator(mode="after")
    def validate_model(self) -> typing.Self:
        if not (self.autogen_policy or self.iam_policy_file):
            raise ValueError("iam_policy_file must be set when autogen_policy is False")

        if not (self.manage_iam_role or self.iam_role_arn):
            raise ValueError("iam_role_arn must be set when manage_iam_role is False")

        if bool(self.subnet_ids) != bool(self.security_group_ids):
            raise ValueError("subnet_ids and security_group_ids must be set together")

        return self


class ChaliceStageConfig(ChaliceLambdaConfig, pydantic.BaseModel):
    api_gateway_stage: str = chalice.constants.DEFAULT_APIGATEWAY_STAGE_NAME

    api_gateway_custom_domain: ChaliceAPIGatewayCustomDomainConfig | None = None
    websocket_api_custom_domain: ChaliceAPIGatewayCustomDomainConfig | None = None

    automatic_layer: bool = False
    minimum_compression_size: int | None = pydantic.Field(
        default=None,
        ge=chalice.constants.MIN_COMPRESSION_SIZE,
        le=chalice.constants.MAX_COMPRESSION_SIZE,
    )
    xray: bool = False
    lambda_functions: dict[str, ChaliceLambdaConfig] | None = None


class ChaliceRootConfig(ChaliceStageConfig, pydantic.BaseModel):
    api_gateway_endpoint_type: typing.Literal["EDGE", "REGIONAL", "PRIVATE"] = chalice.constants.DEFAULT_ENDPOINT_TYPE
    api_gateway_endpoint_vpce: list[str] | str | None = None
    api_gateway_policy_file: pydantic.FilePath | None = None

    stages: dict[str, ChaliceStageConfig] | None = None

    @pydantic.model_validator(mode="after")
    def validate_model(self) -> typing.Self:
        if self.api_gateway_endpoint_type == "PRIVATE" and not self.api_gateway_endpoint_vpce:
            raise ValueError("api_gateway_endpoint_vpce must be set when api_gateway_endpoint_type is PRIVATE")

        return self


class ChaliceConfig(ChaliceRootConfig, pydantic.BaseModel):
    version: typing.Literal["2.0"] = "2.0"
    app_name: str


class InfraConfig(pydantic_settings.BaseSettings):
    ecr_repo_name: str = "notico"
    lambda_name: str = "notico-lambda"
    s3_bucket_name: str = "notico-s3"

    queue_name: str = "notico-queue.fifo"
    queue_visibility_timeout_second: int = 2 * 60
    queue_max_receive_count: int = 5
    dlq_name: str = "notico-dlq.fifo"
    dlq_visibility_timeout_second: int = 2 * 60


class ServiceConfig(pydantic_settings.BaseSettings):
    timeout: float = 3.0

    def is_configured(self) -> bool:
        target_fields = set(self.model_fields) - set(self.model_computed_fields)
        return all(getattr(self, field) for field in target_fields)

    def get_session(self) -> httpx.Client:
        raise NotImplementedError("This method must be implemented in the subclass.")


class ToastConfig(ServiceConfig, pydantic_settings.BaseSettings):
    domain: str | None = None
    api_ver: str | None = None
    app_key: str | None = None
    secret_key: pydantic.SecretStr | None = None
    sender_key: pydantic.SecretStr | None = None

    def get_base_url(self, service: AllowedToastServices) -> str:
        return urllib.parse.urljoin(self.domain, f"/{service}/{self.api_ver}/appkeys/{self.app_key}/")

    def get_session(self, service: AllowedToastServices) -> httpx.Client:  # type: ignore[override]
        return httpx.Client(
            base_url=self.get_base_url(service),
            headers={
                "X-Secret-Key": self.secret_key.get_secret_value(),
                "Content-Type": "application/json;charset=UTF-8",
            },
            timeout=self.timeout,
            event_hooks={"request": [log_request], "response": [log_response]},
        )

    @pydantic.field_serializer("secret_key", "sender_key", when_used="json-unless-none")
    def dump_secret(self, v: pydantic.SecretStr) -> str:
        return v.get_secret_value()


class FirebaseConfig(ServiceConfig, pydantic_settings.BaseSettings):
    certificate: pydantic.SecretStr | None = None
    _app: firebase_admin.App | None = None

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    def get_session(self) -> firebase_admin.App | None:  # type: ignore[override]
        if not self._app:
            with contextlib.suppress(ValueError):
                credential = firebase_admin.credentials.Certificate(cert=self.certificate.get_secret_value())
                self._app = firebase_admin.initialize_app(credential=credential)

        return self._app

    @pydantic.field_serializer("certificate", when_used="json-unless-none")
    def dump_secret(self, v: pydantic.SecretStr) -> str:
        return v.get_secret_value()


class TelegramConfig(ServiceConfig, pydantic_settings.BaseSettings):
    bot_token: pydantic.SecretStr | None = None

    def get_session(self) -> httpx.Client:
        return httpx.Client(
            base_url=f"https://api.telegram.org/bot{self.bot_token.get_secret_value()}/",
            headers={"Content-Type": "application/json;charset=UTF-8"},
            timeout=self.timeout,
            event_hooks={"request": [log_request], "response": [log_response]},
        )

    @pydantic.field_serializer("bot_token", when_used="json-unless-none")
    def dump_secret(self, v: pydantic.SecretStr) -> str:
        return v.get_secret_value()


class SlackConfig(ServiceConfig, pydantic_settings.BaseSettings):
    channel: str | None = None
    token: pydantic.SecretStr | None = None

    @pydantic.field_serializer("token", when_used="json-unless-none")
    def dump_secret(self, v: pydantic.SecretStr) -> str:
        return v.get_secret_value()


class Config(pydantic_settings.BaseSettings):
    project_name: str = "notico"

    chalice: ChaliceRootConfig = pydantic.Field(default_factory=ChaliceRootConfig)
    infra: InfraConfig = pydantic.Field(default_factory=InfraConfig)
    toast: ToastConfig = pydantic.Field(default_factory=ToastConfig)
    firebase: FirebaseConfig = pydantic.Field(default_factory=FirebaseConfig)
    slack: SlackConfig = pydantic.Field(default_factory=SlackConfig)
    telegram: TelegramConfig = pydantic.Field(default_factory=TelegramConfig)

    model_config = pydantic_settings.SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        arbitrary_types_allowed=True,
    )

    @property
    def env_dict(self) -> dict[str, str]:
        settings_dict: dict[str, typing.Any] = self.model_dump(
            mode="json",
            by_alias=True,
            exclude=["chalice"],
            exclude_unset=True,
            exclude_none=True,
        )
        result_dict: dict[str, str] = {}

        if not (delimiters := self.model_config.get("env_nested_delimiter")):
            raise ValueError("env_nested_delimiter must be set in model_config")

        def _flatten_dict(d: dict, prefix: str = "") -> None:
            for k, v in d.items():
                key = f"{prefix}{delimiters}{k}" if prefix else k
                if isinstance(v, dict):
                    _flatten_dict(v, key)
                elif isinstance(v, str):
                    result_dict[key] = v
                else:
                    result_dict[key] = json.dumps(v)

        _flatten_dict(settings_dict)
        return result_dict

    @property
    def chalice_config(self) -> ChaliceConfig:
        return ChaliceConfig(
            app_name=self.project_name,
            environment_variables=self.env_dict,
            **self.chalice.model_dump(mode="python", exclude_unset=True, exclude_none=True),
        )


config = Config()
