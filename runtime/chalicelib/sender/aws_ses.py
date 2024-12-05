import typing

import botocore.exceptions
import chalicelib.aws_resource
import chalicelib.sender.__interface__ as sender_interface
import chalicelib.util.type_util as type_util
import jinja2
import pydantic

if typing.TYPE_CHECKING:
    import mypy_boto3_ses.client
    import mypy_boto3_ses.type_defs


class AWSSESRequest(pydantic.BaseModel):
    # The email address of the sender. It should be in the format of "Sender Name <sender@example.com>"
    from_address: pydantic.EmailStr
    # The email address of the recipient.
    to_addresses: list[pydantic.EmailStr]

    title: str
    body: str

    def send(self) -> list | None:
        # Because if you send it to multiple people at once,
        # the e-mail addresses of the people you send with might be exposed to each other.
        # So, we send it one by one.
        result: list[dict[str, str | bool | None]] = []

        for to_address in self.to_addresses:
            try:
                response: "mypy_boto3_ses.type_defs.SendEmailResponseTypeDef" = (
                    chalicelib.aws_resource.ses_client.send_email(
                        Source=self.from_address,
                        Destination={"ToAddresses": [to_address]},
                        Message={
                            "Subject": {"Charset": "UTF-8", "Data": self.title},
                            "Body": {"Html": {"Charset": "UTF-8", "Data": self.body}},
                        },
                    )
                )
                result.append({"succeed": True, "message_id": response.get("MessageId", None)})
            except Exception as e:
                failed_reason = str(e)
                if isinstance(e, botocore.exceptions.HTTPClientError):
                    failed_reason = e.response.get("Error", {}).get("Message", None) or failed_reason
                result.append({"succeed": False, "reason": failed_reason})

        return result


class AWSSESSendRequest(sender_interface.NotificationSendRequest):
    REQUIRED_SHARED_FIELDS: typing.ClassVar[set[str]] = {"from", "title"}

    @pydantic.field_validator("shared_context", mode="before")
    @classmethod
    def validate_shared_context(cls, v: type_util.ContextType) -> type_util.ContextType:
        if all(k not in v for k in cls.REQUIRED_SHARED_FIELDS):
            raise ValueError("shared_context missing required fields")
        return v

    def to_aws_ses_request(self) -> list[AWSSESRequest]:
        title_template = self.shared_context["title"]
        body_template = chalicelib.aws_resource.S3ResourcePath.email_template.download(
            code=self.template_code,
        ).decode("utf-8")

        return [
            AWSSESRequest.model_validate(
                obj={
                    "from_address": self.shared_context["from"],
                    "to_addresses": [send_to],
                    "title": jinja2.Template(title_template).render(personalized_data),
                    "body": jinja2.Template(body_template).render(personalized_data),
                }
            )
            for send_to, personalized_data in self.personalized_context.items()
        ]


def send_notification(request: AWSSESSendRequest | dict) -> list[list | None]:
    parsed_request = AWSSESSendRequest.model_validate(request) if isinstance(request, dict) else request
    return [aws_ses_request.send() for aws_ses_request in parsed_request.to_aws_ses_request()]


sender_patterns = {
    "aws_ses": send_notification,
}
