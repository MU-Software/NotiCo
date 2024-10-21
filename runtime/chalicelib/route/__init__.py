import pathlib
import typing

import chalice.app
import chalicelib.util.import_util as import_util
import chalicelib.util.type_util as type_util


def register_route(app: chalice.app.Chalice) -> None:
    registered_routes: dict[str, set[type_util.HttpMethodType]] = {}

    for path in pathlib.Path(__file__).parent.glob("*.py"):
        if path.stem.startswith("__") or not (
            patterns := typing.cast(
                type_util.RouteCollectionType,
                getattr(
                    import_util.load_module(path),
                    "route_patterns",
                    None,
                ),
            )
        ):
            continue

        for pattern, methods, handler in patterns:
            if pattern in registered_routes and (_mtd := registered_routes[pattern] & set(methods)):
                raise ValueError(f"Route {pattern} with methods {_mtd} is already registered")

            app.route(path=pattern, methods=methods)(handler)
            registered_routes.setdefault(pattern, set()).update(methods)
