import pathlib
import typing

import chalicelib.util.import_util as import_util

_SenderCollectionType = dict[str, typing.Callable]
senders: _SenderCollectionType = {}

for _path in pathlib.Path(__file__).parent.glob("*.py"):
    if _path.stem.startswith("__") or not (
        _patterns := typing.cast(
            _SenderCollectionType,
            getattr(
                import_util.load_module(_path),
                "sender_patterns",
                None,
            ),
        )
    ):
        continue

    if _duplicated := senders.keys() & _patterns.keys():
        raise ValueError(f"Sender {_duplicated} is already registered")
    senders.update(_patterns)
