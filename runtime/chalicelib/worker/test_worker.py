import typing

import chalice.app

if typing.TYPE_CHECKING:
    # As chalice.local is not available on lambda runtime,
    # We prevent ImportError by using typing.TYPE_CHECKING
    import chalice.local


def test_handler(event: chalice.app.SQSEvent) -> dict[str, typing.Any]:
    context: "chalice.local.LambdaContext" = event.context
    print(event)
    print(dir(event))
    print(event.to_dict())
    print(context)
    return event.to_dict()


worker_patterns = {
    "test_handler": test_handler,
}
