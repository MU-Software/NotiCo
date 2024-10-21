import functools
import typing

Param = typing.ParamSpec("Param")
RetType = typing.TypeVar("RetType")


class RetriesFailedException(Exception):
    pass


def retry(func: typing.Callable[Param, RetType]) -> typing.Callable[Param, RetType]:
    @functools.wraps(wrapped=func)
    def wrapper(*args: Param.args, **kwargs: Param.kwargs) -> RetType:
        retry_count: int = getattr(args[0] if args else kwargs["self"], "retry_count", 3)
        ExceptionClass: type = getattr(args[0] if args else kwargs["self"], "exc_cls", RetriesFailedException)
        exc: Exception | None = None
        for _ in range(retry_count):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                exc = e
        raise ExceptionClass(f"Failed after {retry_count} times") from exc

    return wrapper
