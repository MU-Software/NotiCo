import enum
import typing

import boto3
import chalicelib.config

if typing.TYPE_CHECKING:
    import mypy_boto3_s3.client
    import mypy_boto3_ses.client
    import mypy_boto3_sqs.client


ses_client: "mypy_boto3_ses.client.SESClient" = boto3.client(service_name="ses")
sqs_client: "mypy_boto3_sqs.client.SQSClient" = boto3.client(service_name="sqs")
s3_client: "mypy_boto3_s3.client.S3Client" = boto3.client(service_name="s3")


class S3ResourcePath(enum.StrEnum):
    email_template = "email/template/{filename}"

    def as_path(self, filename: str) -> str:
        return self.value.format(filename=filename)

    def download(self, conf: chalicelib.config.Config, filename: str) -> bytes:
        return s3_client.get_object(Bucket=conf.infra.s3_bucket_name, Key=self.as_path(filename))["Body"].read()
