import chalice.app

health_check_api = chalice.app.Blueprint(__name__)


@health_check_api.route("/readyz", methods=["GET"])
def readyz() -> dict[str, str]:
    return {"status": "ok"}


@health_check_api.route("/livez", methods=["GET"])
def livez() -> dict[str, str]:
    return {"status": "ok"}


blueprints: dict[str, chalice.app.Blueprint] = {"/health": health_check_api}
