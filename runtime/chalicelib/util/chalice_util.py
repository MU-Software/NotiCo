import functools
import traceback
import typing

import chalice.app

Param = typing.ParamSpec("Param")
RetType = typing.TypeVar("RetType")
ReqHandlerType = typing.Callable[[chalice.app.Request], chalice.app.Response]


def exception_catcher(func: typing.Callable[Param, RetType]) -> typing.Callable[Param, RetType]:
    @functools.wraps(wrapped=func)
    def wrapper(*args: Param.args, **kwargs: Param.kwargs) -> RetType:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise chalice.app.ChaliceUnhandledError(str(e)) from e

    return wrapper


def exception_handler_middleware(request: chalice.app.Request, get_response: ReqHandlerType) -> chalice.app.Response:
    try:
        return get_response(request)
    except chalice.app.ChaliceUnhandledError as e:
        traceback_msg = "".join(traceback.format_exception(e.__cause__ or e))
        return chalice.app.Response(status_code=500, body={"traceback": traceback_msg})
    except Exception as e:
        traceback_msg = "".join(traceback.format_exception(e))
        return chalice.app.Response(status_code=500, body={"traceback": traceback_msg})
