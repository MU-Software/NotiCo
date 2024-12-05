import chalicelib.util.type_util as type_util
import pydantic


class NotificationSendRequestSharedContext(pydantic.BaseModel):
    from_: str


class NotificationSendRequest(pydantic.BaseModel):
    template_code: str
    shared_context: type_util.ContextType
    personalized_context: dict[str, type_util.ContextType]
