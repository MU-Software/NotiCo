import chalice.app

index_api = chalice.app.Blueprint(__name__)


@index_api.route("/service", methods=["GET"])
def index() -> dict[str, str]:
    return {"service": "notico"}


blueprints: dict[str, chalice.app.Blueprint] = {"/": index_api}
