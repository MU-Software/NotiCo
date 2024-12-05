import pathlib
import typing

import chalicelib.template_manager.__interface__ as template_mgr_interface
import chalicelib.util.import_util as import_util

_TemplateManagerCollectionType = dict[str, template_mgr_interface.TemplateManagerInterface]
template_managers: _TemplateManagerCollectionType = {}

for _path in pathlib.Path(__file__).parent.glob("*.py"):
    if _path.stem.startswith("__") or not (
        _patterns := typing.cast(
            _TemplateManagerCollectionType,
            getattr(
                import_util.load_module(_path),
                "template_manager_patterns",
                None,
            ),
        )
    ):
        continue

    if _duplicated := template_managers.keys() & _patterns.keys():
        raise ValueError(f"Template manager {_duplicated} is already registered")

    template_managers.update(_patterns)
