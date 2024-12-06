import pathlib
import typing

import chalicelib.send_manager.__interface__ as send_mgr_interface
import chalicelib.template_manager.__interface__ as template_mgr_interface
import chalicelib.util.import_util as import_util

_SendManagerCollectionType = dict[
    str,
    send_mgr_interface.SendManagerInterface[
        send_mgr_interface.BaseSendRequest,
        send_mgr_interface.BaseSendRawRequest,
        template_mgr_interface.TemplateManagerInterface,
    ],
]
send_managers: _SendManagerCollectionType = {}

for _path in pathlib.Path(__file__).parent.glob("*.py"):
    if _path.stem.startswith("__") or not (
        _patterns := typing.cast(
            _SendManagerCollectionType,
            getattr(import_util.load_module(_path), "send_manager_patterns", None),
        )
    ):
        continue

    if _duplicated := send_managers.keys() & _patterns.keys():
        raise ValueError(f"Send manager {_duplicated} is already registered")

    send_managers.update(_patterns)
