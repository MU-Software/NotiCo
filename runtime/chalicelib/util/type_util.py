import typing

import pydantic

HttpMethodType = typing.Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE", "CONNECT"]

AllowedBasicValueTypes = str | int | float | bool | list | dict | None
ContextType = dict[str, AllowedBasicValueTypes]
TemplateType = dict[str, AllowedBasicValueTypes]


class NotiCoSQSMessage(pydantic.BaseModel):
    worker_action: str
