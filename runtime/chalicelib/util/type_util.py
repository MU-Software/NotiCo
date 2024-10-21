import typing

import pydantic

HttpMethodType = typing.Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE", "CONNECT"]
RouteInfoType = tuple[str, list[HttpMethodType], typing.Callable]
RouteCollectionType = list[RouteInfoType]


class NotiCoSQSMessage(pydantic.BaseModel):
    worker_action: str
