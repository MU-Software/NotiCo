import pathlib
import typing

import chalice.app
import chalicelib.util.import_util as import_util


def register_blueprints(app: chalice.app.Chalice) -> None:
    for bps in typing.cast(
        list[chalice.app.Blueprint],
        import_util.auto_import_patterns(pattern="blueprints", file_prefix="", dir=pathlib.Path(__file__).parent),
    ):
        for bp in bps:
            app.register_blueprint(blueprint=bp, url_prefix=bp.url_prefix)
