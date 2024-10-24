import json
import typing

import chalicelib.sender as sender_module

if typing.TYPE_CHECKING:
    import mypy_boto3_sqs.type_defs


def notification_sender(record: "mypy_boto3_sqs.type_defs.MessageTypeDef") -> dict[str, typing.Any]:
    worker_payload = json.loads(record["body"])["worker_payload"]
    sender = sender_module.senders[worker_payload["sender_type"]]
    return sender(worker_payload["sender_payload"])


worker_patterns = {
    "notification_sender": notification_sender,
}
