import typing

import boto3

if typing.TYPE_CHECKING:
    import mypy_boto3_ses.client
    import mypy_boto3_sqs.client


ses_client: "mypy_boto3_ses.client.SESClient" = boto3.client(service_name="ses")
sqs_client: "mypy_boto3_sqs.client.SQSClient" = boto3.client(service_name="sqs")
