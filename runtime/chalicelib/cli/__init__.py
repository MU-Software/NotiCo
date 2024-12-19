import pathlib
import typing

import chalicelib.util.import_util as import_util
import typer

typer_app = typer.Typer()

_cli_patterns: list[list[typing.Callable]] = import_util.auto_import_patterns(
    pattern="cli_funcs",
    file_prefix="",
    dir=pathlib.Path(__file__).parent,
)
for _cli_funcs in _cli_patterns:
    for _cli_func in _cli_funcs:
        typer_app.command()(_cli_func)
