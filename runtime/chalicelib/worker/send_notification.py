import json
import logging
import traceback
import typing

import chalicelib.aws_resource

if typing.TYPE_CHECKING:
    import mypy_boto3_sqs.client
    import mypy_boto3_sqs.type_defs

logger = logging.getLogger(__name__)


def notification_sender(events: "mypy_boto3_sqs.type_defs.MessageTypeDef") -> dict[str, typing.Any]:
    logger.info(events)
    for event in events["Records"]:
        # Get task message from event
        task_receipt_handle: str = event["receiptHandle"]

        try:
            # Remove message
            chalicelib.aws_resource.sqs_client.delete_message(
                # TODO: FIXME: SQS_URL is not defined
                # QueueUrl=SQS_URL,
                QueueUrl="",
                ReceiptHandle=task_receipt_handle,
            )

        except Exception as err:
            logger.error(traceback.format_exception(err), err)
            chalicelib.aws_resource.sqs_client.change_message_visibility(
                # TODO: FIXME: SQS_URL is not defined
                # QueueUrl=SQS_URL,
                QueueUrl="",
                ReceiptHandle=task_receipt_handle,
                VisibilityTimeout=45,  # Make this message visible again after 45 seconds
            )

    # Exit this lambda instance as there's no message in queue
    return {
        "statusCode": 200,
        "event": event,
        "body": json.dumps(
            {
                "message": "NO_TASK_IN_QUEUE",
            }
        ),
    }
