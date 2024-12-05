from __future__ import annotations

import typing

import chalicelib.template_manager.__interface__ as template_mgr_interface
import chalicelib.util.type_util as type_util
import pydantic


class BaseSendRequest(pydantic.BaseModel):
    template_code: str
    shared_context: type_util.ContextType
    personalized_context: dict[str, type_util.ContextType]


class BaseSendRawRequest(pydantic.BaseModel):
    personalized_content: dict[str, type_util.ContextType]


SendRequestType = typing.TypeVar("SendRequestType", bound=BaseSendRequest)
SendRawRequestType = typing.TypeVar("SendRawRequestType", bound=BaseSendRawRequest)
TemplateManagerType = typing.TypeVar("TemplateManagerType", bound=template_mgr_interface.TemplateManagerInterface)


class SendManagerInterface[SendRequestType, SendRawRequestType, TemplateManagerType](typing.Protocol):
    CAN_SEND_RAW_MESSAGE: typing.ClassVar[bool] = False

    @property
    def initialized(self) -> bool: ...

    @property
    def template_manager(self) -> TemplateManagerType: ...

    def send(self, request: SendRequestType) -> dict[str, str | None]: ...

    def send_raw(self, request: SendRawRequestType) -> dict[str, str | None]: ...
