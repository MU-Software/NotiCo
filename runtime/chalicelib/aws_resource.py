import dataclasses
import enum
import functools
import typing

import boto3
import chalicelib.config as config_module

if typing.TYPE_CHECKING:
    import mypy_boto3_s3.client
    import mypy_boto3_ses.client
    import mypy_boto3_sqs.client


ses_client: "mypy_boto3_ses.client.SESClient" = boto3.client(service_name="ses")
sqs_client: "mypy_boto3_sqs.client.SQSClient" = boto3.client(service_name="sqs")
s3_client: "mypy_boto3_s3.client.S3Client" = boto3.client(service_name="s3")


@dataclasses.dataclass
class S3ResourceInfo:
    prefix: str
    extension: str

    def as_path(self, code: str) -> str:
        return self.prefix + f"{code}.{self.extension}"


class S3ResourcePath(enum.Enum):
    email_template = S3ResourceInfo(prefix="email/template/", extension="json")
    telegram_template = S3ResourceInfo(prefix="telegram/template/", extension="json")
    firebase_template = S3ResourceInfo(prefix="firebase/template/", extension="json")

    @functools.cached_property
    def s3_bucket_name(self) -> config_module.InfraConfig:
        return config_module.config.infra.s3_bucket_name

    def download(self, code: str) -> bytes:
        return s3_client.get_object(Bucket=self.s3_bucket_name, Key=self.value.as_path(code))["Body"].read()

    def upload(self, code: str, content: str) -> None:
        s3_client.put_object(Bucket=self.s3_bucket_name, Key=self.value.as_path(code), Body=content)

    def delete(self, code: str) -> None:
        s3_client.delete_object(Bucket=self.s3_bucket_name, Key=self.value.as_path(code))

    def list_objects(self, filter_by_extension: bool = False) -> list[str]:
        return [
            key
            for obj in s3_client.list_objects(Bucket=self.s3_bucket_name, Prefix=self.value.prefix)["Contents"]
            if (key := obj["Key"].replace(self.value.prefix, ""))
            and (not filter_by_extension or key.split(".")[-1] == self.value.extension)
        ]
