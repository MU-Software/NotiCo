from __future__ import annotations

import typing

import chalicelib.template_manager.__interface__ as template_mgr_interface
import chalicelib.util.type_util as type_util
import pydantic


class SendRequest(pydantic.BaseModel):
    template_code: str
    shared_context: type_util.ContextType
    personalized_context: dict[str, type_util.ContextType]


class SendManagerInterface:
    service_name: typing.ClassVar[str]
    template_manager: typing.ClassVar[template_mgr_interface.TemplateManagerInterface]

    initialized: typing.ClassVar[bool]

    def __init_subclass__(cls) -> None:
        type_util.check_classvar_initialized(cls, ["service_name", "template_manager"])

    def send(self, request: SendRequest) -> dict[str, str | None]: ...
