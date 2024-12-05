import chalice
import chalice.app
import chalicelib.template_manager as template_manager
import chalicelib.util.type_util as type_util

template_manager_api = chalice.app.Blueprint(__name__)


@template_manager_api.route("/", methods=["GET"])
def list_template_manager_services() -> dict[str, list[str]]:
    return {"template_managers": [k for k, v in template_manager.template_managers.items() if v.initialized]}


@template_manager_api.route("/{service_name}", methods=["GET"])
def list_templates(service_name: str) -> list[dict[str, str]]:
    if service_name not in template_manager.template_managers:
        raise chalice.NotFoundError(f"Service {service_name} not found")
    return [t.model_dump(mode="json") for t in template_manager.template_managers[service_name].list()]


@template_manager_api.route("/{service_name}/{code}", methods=["GET", "POST", "PUT", "DELETE"])
def crud_template(service_name: str, code: str) -> dict[str, str]:
    request: chalice.app.Request = template_manager_api.current_request
    method: type_util.HttpMethodType = request.method.upper()
    payload: dict[str, str] | None = request.json_body if method in {"POST", "PUT"} else None

    if not (template_mgr := template_manager.template_managers.get(service_name, None)):
        raise chalice.NotFoundError(f"Service {service_name} not found")

    if method == "GET":
        if template_info := template_mgr.retrieve(code):
            return template_info.model_dump(mode="json")
        raise chalice.NotFoundError(f"Template {code} not found")
    elif method == "POST":
        if not payload:
            raise chalice.BadRequestError("Payload is required")
        return template_mgr.create(code, payload).model_dump(mode="json")
    elif method == "PUT":
        if not payload:
            raise chalice.BadRequestError("Payload is required")
        return template_mgr.update(code, payload).model_dump(mode="json")
    elif method == "DELETE":
        template_mgr.delete(code)
        return {"code": code}

    raise chalice.NotFoundError(f"Method {method} is not allowed")


blueprints: dict[str, chalice.app.Blueprint] = {"/template-manager": template_manager_api}
