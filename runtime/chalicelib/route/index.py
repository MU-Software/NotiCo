import pathlib

import chalice.app

runtime_dir = pathlib.Path(__file__).parent.parent.parent
frontend_path = runtime_dir / "frontend" / "admin" / "index.html"

index_api = chalice.app.Blueprint(__name__)
index_api.url_prefix = ""


@index_api.route("/service", methods=["GET"])
def get_service_identity() -> dict[str, str]:
    return {"service": "notico"}


@index_api.route("/admin", methods=["GET"])
def get_admin_frontend() -> str:
    if not frontend_path.exists():
        raise chalice.app.NotFoundError("Admin frontend not found")
    return chalice.app.Response(body=frontend_path.read_text(), headers={"Content-Type": "text/html"})


blueprints: list[chalice.app.Blueprint] = [index_api]
