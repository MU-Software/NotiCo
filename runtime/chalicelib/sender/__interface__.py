import pydantic

ReceiverType = str
AllowedBasicValueTypes = str | int | float | bool | None
AllowedValueTypes = AllowedBasicValueTypes | list[AllowedBasicValueTypes] | dict[str, AllowedBasicValueTypes] | None
ContextType = dict[str, AllowedValueTypes]


class NotificationSendRequestSharedContext(pydantic.BaseModel):
    from_: str


class NotificationSendRequest(pydantic.BaseModel):
    template_code: str
    shared_context: ContextType
    personalized_context: dict[ReceiverType, ContextType]
