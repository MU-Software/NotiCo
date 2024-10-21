import json
import logging
import pathlib
import typing

import chalice.app
import chalicelib.util.import_util as import_util

logger = logging.getLogger(__name__)

_WorkerCollectionType = dict[str, typing.Callable[[chalice.app.SQSEvent], dict[str, typing.Any]]]
_workers: _WorkerCollectionType = {}

for _path in pathlib.Path(__file__).parent.glob("*.py"):
    if _path.stem.startswith("__") or not (
        _patterns := typing.cast(
            _WorkerCollectionType,
            getattr(
                import_util.load_module(_path),
                "worker_patterns",
                None,
            ),
        )
    ):
        continue

    if _duplicated := _workers.keys() & _patterns.keys():
        raise ValueError(f"Worker {_duplicated} is already registered")
    _workers.update(_patterns)


def register_worker(app: chalice.app.Chalice, queue: str) -> None:
    @app.on_sqs_message(queue=queue)
    def handler(event: chalice.app.SQSEvent) -> dict[str, typing.Any]:
        try:
            parsed_event = event.to_dict()
            result = _workers[json.loads(parsed_event["body"])["worker"]](event)
            logger.info(f"Handled event: {parsed_event}")
            return result
        except Exception as e:
            logger.error(f"Failed to handle event: {parsed_event}", exc_info=e)
            return {"error": "Failed to handle event"}
