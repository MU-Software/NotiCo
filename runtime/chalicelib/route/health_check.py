import chalice.app
import chalicelib.util.chalice_util as chalice_util

health_check_api = chalice.app.Blueprint(__name__)
health_check_api.url_prefix = "health"


@health_check_api.route("/readyz", methods=["GET"])
@chalice_util.api_gateway_desc(summary="Readiness probe", description="Check if the service is ready")
@chalice_util.exception_catcher
def readyz() -> dict[str, str]:
    return {"status": "ok"}


@health_check_api.route("/livez", methods=["GET"])
@chalice_util.api_gateway_desc(summary="Liveness probe", description="Check if the service is live")
@chalice_util.exception_catcher
def livez() -> dict[str, str]:
    return {"status": "ok"}


blueprints: list[chalice.app.Blueprint] = [health_check_api]
