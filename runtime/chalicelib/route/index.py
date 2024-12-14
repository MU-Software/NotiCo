import chalice.app
import chalicelib.util.chalice_util as chalice_util

index_api = chalice.app.Blueprint(__name__)
index_api.url_prefix = ""


@index_api.route("/service", methods=["GET"])
@chalice_util.exception_catcher
def get_service_identity() -> dict[str, str]:
    return {"service": "notico"}


blueprints: list[chalice.app.Blueprint] = [index_api]
