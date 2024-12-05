import typing

import pydantic

HttpMethodType = typing.Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE", "CONNECT"]

AllowedBasicValueTypes = str | int | float | bool | None
AllowedValueTypes = AllowedBasicValueTypes | list[AllowedBasicValueTypes] | dict[str, AllowedBasicValueTypes] | None
ContextType = dict[str, AllowedValueTypes]
TemplateType = dict[str, AllowedValueTypes]


class NotiCoSQSMessage(pydantic.BaseModel):
    worker_action: str
