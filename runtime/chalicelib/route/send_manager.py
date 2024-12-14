import typing

import chalice
import chalice.app
import chalicelib.send_manager as send_manager
import chalicelib.send_manager.__interface__ as send_mgr_interface
import chalicelib.util.chalice_util as chalice_util

send_manager_api = chalice.app.Blueprint(__name__)
send_manager_api.url_prefix = "send-manager"


@send_manager_api.route("/", methods=["GET"])
@chalice_util.exception_catcher
def list_send_manager_services() -> list[dict[str, str | bool | dict]]:
    return [
        {
            "name": v.service_name,
            "template_schema": v.template_manager.template_structure_cls.model_json_schema(),
        }
        for v in send_manager.send_managers.values()
        if v.initialized
    ]


@send_manager_api.route("/{service_name}", methods=["POST"])
@chalice_util.exception_catcher
def send_message(service_name: str) -> dict[str, str | None]:
    request: chalice.app.Request = send_manager_api.current_request
    if not (payload := typing.cast(dict[str, str] | None, request.json_body)):
        raise chalice.BadRequestError("Payload not given")

    if not (send_mgr := send_manager.send_managers.get(service_name, None)):
        raise chalice.NotFoundError(f"Service {service_name} not found")

    return send_mgr.send(request=send_mgr_interface.SendRequest.model_validate(payload))


blueprints: list[chalice.app.Blueprint] = [send_manager_api]
