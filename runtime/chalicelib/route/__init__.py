import pathlib
import typing

import chalice.app
import chalicelib.util.chalice_util as chalice_util
import chalicelib.util.import_util as import_util

ROUTE_DIR = pathlib.Path(__file__).parent
RUNTIME_DIR = ROUTE_DIR.parent.parent
FRONTEND_DIR = RUNTIME_DIR / "frontend"
FRONTEND_ADMIN_PATH = FRONTEND_DIR / "admin" / "index.html"


def register_blueprints(app: chalice.app.Chalice) -> None:
    app.register_middleware(func=chalice_util.exception_handler_middleware, event_type="http")

    for bps in typing.cast(
        list[chalice.app.Blueprint],
        import_util.auto_import_patterns(pattern="blueprints", file_prefix="", dir=pathlib.Path(__file__).parent),
    ):
        for bp in bps:
            if bp.url_prefix.startswith("/"):
                raise ValueError(f"URL Prefix must not start with '/': {bp.url_prefix}")

            app.register_blueprint(blueprint=bp, url_prefix=f"/api/v1/{bp.url_prefix}")

    @app.route(path="/", methods=["GET"])
    @app.route(path="/template-manager", methods=["GET"])
    @app.route(path="/send-manager", methods=["GET"])
    def get_admin_frontend() -> str:
        if not FRONTEND_ADMIN_PATH.exists():
            raise chalice.app.NotFoundError("Admin frontend not found")
        return chalice.app.Response(body=FRONTEND_ADMIN_PATH.read_text(), headers={"Content-Type": "text/html"})
