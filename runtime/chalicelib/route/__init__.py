import pathlib
import typing

import chalice.app
import chalicelib.util.import_util as import_util


def register_blueprints(app: chalice.app.Chalice) -> None:
    blueprints: dict[str, chalice.app.Blueprint] = {}

    for path in pathlib.Path(__file__).parent.glob("*.py"):
        if path.stem.startswith("__") or not (
            patterns := typing.cast(
                dict[str, chalice.app.Blueprint],
                getattr(import_util.load_module(path), "blueprints", None),
            )
        ):
            continue

        for url_prefix, blueprint in patterns.items():
            if url_prefix in blueprints:
                raise ValueError(f"URL Prefix {url_prefix} is already registered")

            app.register_blueprint(blueprint=blueprint, url_prefix=url_prefix)
            blueprints[url_prefix] = blueprint
