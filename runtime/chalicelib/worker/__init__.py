import json
import pathlib
import typing

import chalice.app
import chalicelib.config as config_module
import chalicelib.util.import_util as import_util

if typing.TYPE_CHECKING:
    import mypy_boto3_sqs.type_defs

    SQSEventType = typing.TypedDict("SQSEventType", {"Records": list["mypy_boto3_sqs.type_defs.MessageTypeDef"]})
else:
    SQSEventType = dict[str, typing.Any]

_WorkerCollectionType = dict[str, typing.Callable[[chalice.app.Chalice, chalice.app.SQSEvent], dict[str, typing.Any]]]
workers: _WorkerCollectionType = {}

for _path in pathlib.Path(__file__).parent.glob("*.py"):
    if _path.stem.startswith("__") or not (
        _patterns := typing.cast(
            _WorkerCollectionType,
            getattr(import_util.load_module(_path), "worker_patterns", None),
        )
    ):
        continue

    if _duplicated := workers.keys() & _patterns.keys():
        raise ValueError(f"Worker {_duplicated} is already registered")
    workers.update(_patterns)


def register_worker(app: chalice.app.Chalice) -> None:
    @app.on_sqs_message(queue=config_module.config.infra.queue_name)
    def sqs_handler(event: chalice.app.SQSEvent) -> list[dict[str, typing.Any]]:
        parsed_event: SQSEventType = event.to_dict()
        app.log.info(f"{parsed_event=}")

        results: list[dict[str, typing.Any]] = []
        for record in parsed_event["Records"]:
            try:
                worker_name = json.loads(record["body"])["worker"]
                result = workers[worker_name](app, record)
                results.append(result)
            except Exception as e:
                app.log.error(f"Failed to handle event: {record}", exc_info=e)
                results.append({"error": "Failed to handle event"})

        app.log.info(f"{results=}")
        return results
