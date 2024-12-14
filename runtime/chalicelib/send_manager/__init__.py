import pathlib
import typing

import chalicelib.send_manager.__interface__ as send_mgr_interface
import chalicelib.util.import_util as import_util

send_managers: dict[str, send_mgr_interface.SendManagerInterface] = {}

for _mgrs in typing.cast(
    list[list[send_mgr_interface.SendManagerInterface]],
    import_util.auto_import_patterns(pattern="send_managers", file_prefix="", dir=pathlib.Path(__file__).parent),
):
    send_managers.update({mgr.service_name: mgr for mgr in _mgrs})
