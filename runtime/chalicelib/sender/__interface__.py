import chalicelib.config as config_module
import pydantic

ReceiverType = str
AllowedValueTypes = str | int | float
ContextType = dict[str, AllowedValueTypes]


class NotificationSendRequestSharedContext(pydantic.BaseModel):
    from_: str


class NotificationSendRequest(pydantic.BaseModel):
    template_code: str
    shared_context: ContextType
    personalized_context: dict[ReceiverType, ContextType]

    conf: config_module.Config
