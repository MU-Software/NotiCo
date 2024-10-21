import contextlib
import importlib.util
import pathlib
import types
import typing

T = typing.TypeVar("T")


def isiterable(a: typing.Any) -> bool:
    with contextlib.suppress(TypeError):
        return iter(a) is not None
    return False


def load_module(module_path: pathlib.Path) -> types.ModuleType:
    if not module_path.is_file():
        raise ValueError(f"module_path must be file path: {module_path}")

    module_path = module_path.resolve()
    module_name = module_path.stem
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def auto_import_objs(pattern_name: str, file_prefix: str, dir: pathlib.Path) -> list[T]:
    collected_objs: list[T] = []
    for module_path in dir.glob(f"**/{file_prefix}*.py"):
        if module_path.stem.startswith("__"):
            continue

        if obj := typing.cast(T, getattr(load_module(module_path), pattern_name, None)):
            collected_objs.append(obj)
    return collected_objs


def auto_import_patterns(pattern_name: str, file_prefix: str, dir: pathlib.Path) -> list[T]:
    return list(filter(isiterable, auto_import_objs(pattern_name, file_prefix, dir)))
