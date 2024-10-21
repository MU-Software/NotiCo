import typing

import botocore.exceptions
import chalicelib.aws_resource
import pydantic

if typing.TYPE_CHECKING:
    import mypy_boto3_ses.client
    import mypy_boto3_ses.type_defs


class AWSSESRequest(pydantic.BaseModel):
    # The email address of the sender. It should be in the format of "Sender Name <sender@example.com>"
    from_address: pydantic.EmailStr
    # The email address of the recipient. It should be a string, not a list,
    # because if you send it to multiple people at once,
    # the e-mail addresses of the people you send with might be exposed to each other.
    to_address: pydantic.EmailStr
    subject: str
    payload: str

    def send(self) -> str | None:
        try:
            response: "mypy_boto3_ses.type_defs.SendEmailResponseTypeDef" = (
                chalicelib.aws_resource.ses_client.send_email(
                    Source=self.from_address,
                    Destination={"ToAddresses": [self.to_address]},
                    Message={
                        "Subject": {"Charset": "UTF-8", "Data": self.subject},
                        "Body": {"Html": {"Charset": "UTF-8", "Data": self.payload}},
                    },
                )
            )
            return response.get("MessageId", None)
        except Exception as e:
            if isinstance(e, botocore.exceptions.HTTPClientError):
                raise Exception(e.response.get("Error", {}).get("Message", None) or str(e)) from e
            raise Exception from e
