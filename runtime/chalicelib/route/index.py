import chalicelib.util.type_util as type_util


def index() -> dict[str, str]:
    return {"service": "notico"}


route_patterns: type_util.RouteInfoType = [
    ("/", ["GET"], index),
]
