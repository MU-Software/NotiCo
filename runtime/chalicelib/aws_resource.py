import dataclasses
import enum
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
s3_bucket_name: str = config_module.config.infra.s3_bucket_name


@dataclasses.dataclass(frozen=True)
class S3ResourceInfo:
    prefix: str
    extension: str

    def as_path(self, template_code: str) -> str:
        return self.prefix + f"{template_code}.{self.extension}"


class S3ResourcePath(enum.Enum):
    email_template = S3ResourceInfo(prefix="email/template/", extension="json")
    telegram_template = S3ResourceInfo(prefix="telegram/template/", extension="json")
    firebase_template = S3ResourceInfo(prefix="firebase/template/", extension="json")

    def download(self, template_code: str) -> bytes:
        return s3_client.get_object(Bucket=s3_bucket_name, Key=self.value.as_path(template_code))["Body"].read()

    def upload(self, template_code: str, content: str) -> None:
        s3_client.put_object(Bucket=s3_bucket_name, Key=self.value.as_path(template_code), Body=content.encode())

    def delete(self, template_code: str) -> None:
        s3_client.delete_object(Bucket=s3_bucket_name, Key=self.value.as_path(template_code))

    def list_objects(self, filter_by_extension: bool = False) -> list[str]:
        if objs := s3_client.list_objects(Bucket=s3_bucket_name, Prefix=self.value.prefix).get("Contents", None):
            return [
                key
                for obj in objs
                if (key := obj["Key"].replace(self.value.prefix, ""))
                and (not filter_by_extension or key.split(".")[-1] == self.value.extension)
            ]
        return []
