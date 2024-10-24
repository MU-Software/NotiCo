import functools
import typing
import urllib.parse

import httpx
import pydantic
import pydantic_settings

AllowedToastServices = typing.Literal["alimtalk"]


class InfraConfig(pydantic_settings.BaseSettings):
    ecr_repo_name: str = "notico"
    lambda_name: str = "notico-lambda"
    s3_bucket_name: str = "notico-s3"

    queue_name: str = "notico-queue.fifo"
    queue_visibility_timeout_second: int = 2 * 60
    queue_max_receive_count: int = 5
    dlq_name: str = "notico-dlq.fifo"
    dlq_visibility_timeout_second: int = 2 * 60


class _ServiceConfig(pydantic_settings.BaseSettings):
    def is_configured(self) -> bool:
        target_fields = set(self.model_fields) - set(self.model_computed_fields)
        return all(getattr(self, field) for field in target_fields)


class ToastConfig(_ServiceConfig, pydantic_settings.BaseSettings):
    domain: str | None = None
    api_ver: str | None = None
    app_key: str | None = None
    secret_key: pydantic.SecretStr | None = None
    sender_key: pydantic.SecretStr | None = None
    timeout: float = 3.0

    def get_base_url(self, service: AllowedToastServices) -> str:
        return urllib.parse.urljoin(self.domain, f"/{service}/{self.api_ver}/appkeys/{self.app_key}/")

    def get_session(self, service: AllowedToastServices) -> httpx.Client:
        return httpx.Client(
            base_url=self.get_base_url(service),
            headers={
                "X-Secret-Key": self.secret_key.get_secret_value(),
                "Content-Type": "application/json;charset=UTF-8",
            },
            timeout=self.timeout,
        )


class FirebaseConfig(_ServiceConfig, pydantic_settings.BaseSettings):
    certificate: pydantic.SecretStr | None = None


class SlackConfig(_ServiceConfig, pydantic_settings.BaseSettings):
    channel: str | None = None
    token: pydantic.SecretStr | None = None


class Config(pydantic_settings.BaseSettings):
    infra: InfraConfig = pydantic.Field(default_factory=InfraConfig)
    toast: ToastConfig = pydantic.Field(default_factory=ToastConfig)
    firebase: FirebaseConfig = pydantic.Field(default_factory=FirebaseConfig)
    slack: SlackConfig = pydantic.Field(default_factory=SlackConfig)

    env_vars: dict[str, str] = pydantic.Field(default_factory=dict)


@functools.lru_cache(maxsize=1)
def get_config() -> Config:
    return Config(_env_nested_delimiter="__", _case_sensitive=False)
