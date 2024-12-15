import json
import logging
import pathlib
import typing

import chalice.app
import chalicelib.config as config_module
import chalicelib.util.import_util as import_util

WorkerType = typing.Callable[[chalice.app.SQSRecord], dict[str, typing.Any]]

logger = logging.getLogger(__name__)
workers: dict[str, WorkerType] = {}
worker_handler_blueprint = chalice.app.Blueprint(__name__)

for _workers in typing.cast(
    list[list[WorkerType]],
    import_util.auto_import_patterns(pattern="workers", file_prefix="", dir=pathlib.Path(__file__).parent),
):
    _func_names = {worker.__name__ for worker in _workers}
    if _duplicated := _func_names & workers.keys():
        raise ValueError(f"Worker {_duplicated} is already registered")

    workers.update({worker.__name__: worker for worker in _workers})


@worker_handler_blueprint.on_sqs_message(queue=config_module.config.infra.queue_name)
def sqs_handler(event: chalice.app.SQSEvent) -> list[dict[str, typing.Any]]:
    results: list[dict[str, typing.Any]] = []
    for record in event:
        try:
            results.append(workers[json.loads(record.body)["worker"]](record))
        except Exception as e:
            logger.error(f"Failed to handle event: {record}", exc_info=e)
            results.append({"error": "Failed to handle event"})

    logger.info(f"{results=}")
    return results


def register_worker(app: chalice.app.Chalice) -> None:
    app.register_blueprint(worker_handler_blueprint)
