import chalicelib.util.type_util as type_util


def readyz() -> dict[str, str]:
    return {"status": "ok"}


def livez() -> dict[str, str]:
    return {"status": "ok"}


route_patterns: type_util.RouteInfoType = [
    ("/readyz", ["GET"], readyz),
    ("/livez", ["GET"], livez),
]
