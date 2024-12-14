import pathlib
import typing

import chalicelib.template_manager.__interface__ as template_mgr_interface
import chalicelib.util.import_util as import_util

template_managers: dict[str, template_mgr_interface.TemplateManagerInterface] = {}

for _mgrs in typing.cast(
    list[list[template_mgr_interface.TemplateManagerInterface]],
    import_util.auto_import_patterns(pattern="template_managers", file_prefix="", dir=pathlib.Path(__file__).parent),
):
    template_managers.update({mgr.service_name: mgr for mgr in _mgrs})
