import pathlib
import typing

import chalice.app
import chalicelib.util.import_util as import_util

_WorkerCollectionType = dict[str, typing.Callable[[chalice.app.SQSEvent], dict[str, typing.Any]]]
workers: _WorkerCollectionType = {}

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

    if _duplicated := workers.keys() & _patterns.keys():
        raise ValueError(f"Worker {_duplicated} is already registered")
    workers.update(_patterns)
