import contextlib
import logging
import typing
import urllib.parse

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


class TelegramConfig(ServiceConfig, pydantic_settings.BaseSettings):
    bot_token: pydantic.SecretStr | None = None

    def get_session(self) -> httpx.Client:
        return httpx.Client(
            base_url=f"https://api.telegram.org/bot{self.bot_token.get_secret_value()}/",
            headers={"Content-Type": "application/json;charset=UTF-8"},
            timeout=self.timeout,
            event_hooks={"request": [log_request], "response": [log_response]},
        )


class SlackConfig(ServiceConfig, pydantic_settings.BaseSettings):
    channel: str | None = None
    token: pydantic.SecretStr | None = None


class Config(pydantic_settings.BaseSettings):
    infra: InfraConfig = pydantic.Field(default_factory=InfraConfig)
    toast: ToastConfig = pydantic.Field(default_factory=ToastConfig)
    firebase: FirebaseConfig = pydantic.Field(default_factory=FirebaseConfig)
    slack: SlackConfig = pydantic.Field(default_factory=SlackConfig)
    telegram: TelegramConfig = pydantic.Field(default_factory=TelegramConfig)

    env_vars: dict[str, str] = pydantic.Field(default_factory=dict)


config = Config(_env_nested_delimiter="__", _case_sensitive=False)
