import contextlib
import datetime
import json
import logging
import typing

import chalicelib.config as config_module
import firebase_admin
import firebase_admin.credentials
import firebase_admin.messaging
import pydantic

logger = logging.getLogger(__name__)


def _stringify_data(data: typing.Any) -> str:
    with contextlib.suppress(Exception):
        return json.dumps(data)
    with contextlib.suppress(Exception):
        return str(data)
    return ""


def _jsonify_data(data: dict[typing.Any, typing.Any]) -> dict[str, str]:
    result = {}
    for k, v in data.items():
        stringified_key = _stringify_data(k)

        if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
            result[stringified_key] = v.isoformat()
            if isinstance(v, datetime.datetime):
                result[f"{stringified_key}_timestamp"] = str(v.timestamp())
        else:
            result[stringified_key] = _stringify_data(v)

    return result


class FirebaseCloudMessaging(pydantic.BaseModel):
    title: str = ""
    body: str = ""
    data: dict = pydantic.Field(default={"click_action": "FLUTTER_NOTIFICATION"})

    topic: str | None = None
    target_tokens: list[str] | None = None
    condition: str | None = None

    certificate: pydantic.SecretStr
    android: firebase_admin.messaging.AndroidConfig | None = None
    apns: firebase_admin.messaging.APNSConfig | None = None
    webpush: firebase_admin.messaging.WebpushConfig | None = None
    fcm_options: firebase_admin.messaging.FCMOptions | None = None

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    @pydantic.field_validator("data", mode="before")
    def validate_data(cls, data: dict) -> dict:
        # All keys and values in data must be a string in firebase cloud messaging.
        # We'll try to type cast all values to json compatible string.
        return _jsonify_data(data)

    @property
    def message_payloads(self) -> list[firebase_admin.messaging.Message]:
        notification = (
            firebase_admin.messaging.Notification(title=self.title, body=self.body)
            if any((self.title, self.body))
            else None
        )

        return [
            firebase_admin.messaging.Message(
                data=self.data,
                notification=notification,
                token=target_token,
                topic=self.topic,
                # specify receiver by using multiple topic subscription status.
                # 'condition' shapes like this
                # >>> condition = "'stock-GOOG' in topics || 'industry-tech' in topics"
                condition=self.condition,
                android=self.android,
                apns=self.apns,
                webpush=self.webpush,
                fcm_options=self.fcm_options,
            )
            for target_token in self.target_tokens
        ]

    def send(self) -> str:
        if not config_module.config.firebase.is_configured():
            raise ValueError("Firebase configuration is not set up properly.")

        with contextlib.suppress(ValueError):
            firebase_admin.initialize_app(
                credential=firebase_admin.credentials.Certificate(
                    cert=config_module.config.firebase.certificate.get_secret_value(),
                )
            )

        # response is a message ID string.
        response: str = firebase_admin.messaging.send_all(self.message_payloads)
        logger.info(f"Successfully sent message: {response}")
        return response
