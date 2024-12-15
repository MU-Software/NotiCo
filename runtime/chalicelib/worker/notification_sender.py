import functools
import typing

import chalice.app
import chalicelib.send_manager as send_manager
import chalicelib.send_manager.__interface__ as send_mgr_interface
import pydantic


class WorkerPayload(pydantic.BaseModel):
    sender_type: str
    sender_payload: dict[str, typing.Any]

    @functools.cached_property
    def send_manager(self) -> send_mgr_interface.SendManagerInterface:
        return send_manager.send_managers[self.sender_type]

    @functools.cached_property
    def send_request_payload(self) -> send_mgr_interface.SendRequest:
        return self.send_manager.send_request_cls.model_validate(self.sender_payload)

    @pydantic.field_validator("sender_type", mode="before")
    @classmethod
    def validate_sender_type(cls, value: str) -> str:
        if value not in send_manager.send_managers:
            raise ValueError(f"Invalid sender type: {value}")
        return value

    @pydantic.model_validator(mode="after")
    def validate_sender_payload(self) -> typing.Self:
        self.send_request_payload
        return self

    def send(self) -> dict[str, str]:
        return self.send_manager.send(self.send_request_payload)


class SQSRecordBody(pydantic.BaseModel):
    worker: str
    worker_payload: WorkerPayload


def notification_sender(record: chalice.app.SQSRecord) -> dict[str, str]:
    return SQSRecordBody.model_validate_json(record.body).worker_payload.send()


workers = [notification_sender]
