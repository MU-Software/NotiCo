import typing

import chalice
import chalice.app
import chalicelib.template_manager as template_manager
import chalicelib.util.chalice_util as chalice_util

HttpMethodType = typing.Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE", "CONNECT"]

template_manager_api = chalice.app.Blueprint(__name__)
template_manager_api.url_prefix = "template-manager"


@template_manager_api.route("/", methods=["GET"])
@chalice_util.exception_catcher
def list_template_manager_services() -> list[dict[str, str]]:
    return [
        {
            "name": v.service_name,
            "template_schema": v.template_structure_cls.model_json_schema(),
        }
        for v in template_manager.template_managers.values()
        if v.initialized
    ]


@template_manager_api.route("/{service_name}", methods=["GET"])
@chalice_util.exception_catcher
def list_templates(service_name: str) -> list[dict[str, str]]:
    if service_name not in template_manager.template_managers:
        raise chalice.NotFoundError(f"Service {service_name} not found")
    return [t.model_dump(mode="json") for t in template_manager.template_managers[service_name].list()]


@template_manager_api.route("/{service_name}/{template_code}", methods=["GET", "POST", "PUT", "DELETE"])
@chalice_util.exception_catcher
def crud_template(service_name: str, template_code: str) -> dict[str, str]:
    request: chalice.app.Request = template_manager_api.current_request
    method: HttpMethodType = request.method.upper()
    payload: dict[str, str] | None = request.json_body if method in {"POST", "PUT"} else None

    if not (template_mgr := template_manager.template_managers.get(service_name, None)):
        raise chalice.NotFoundError(f"Service {service_name} not found")

    if method == "GET":
        if template_info := template_mgr.retrieve(template_code):
            return template_info.model_dump(mode="json")
        raise chalice.NotFoundError(f"Template {template_code} not found")
    elif method == "POST":
        if not (payload and (template_data := payload.get("template"))):
            raise chalice.BadRequestError("Payload is required")
        return template_mgr.create(template_code, template_data).model_dump(mode="json")
    elif method == "PUT":
        if not (payload and (template_data := payload.get("template"))):
            raise chalice.BadRequestError("Payload is required")
        return template_mgr.update(template_code, template_data).model_dump(mode="json")
    elif method == "DELETE":
        template_mgr.delete(template_code)
        return {"template_code": template_code}

    raise chalice.NotFoundError(f"Method {method} is not allowed")


@template_manager_api.route("/{service_name}/{template_code}/render", methods=["POST"])
@chalice_util.exception_catcher
def render_template(service_name: str, template_code: str) -> dict[str, str]:
    request: chalice.app.Request = template_manager_api.current_request
    requested_content_type: str = request.headers.get("Accept", "text/html")

    if not (payload := typing.cast(dict[str, str] | None, request.json_body)):
        raise chalice.BadRequestError("Payload not given")

    if not (template_mgr := template_manager.template_managers.get(service_name, None)):
        raise chalice.NotFoundError(f"Service {service_name} not found")

    if "application/json" in requested_content_type:
        return {"render_result": template_mgr.render(template_code, payload)}

    return chalice.app.Response(
        headers={"Content-Type": "text/html"},
        body=template_mgr.render_html(
            template_code=template_code,
            context=payload,
            not_defined_variable_handling=payload.get("not_defined_variable_handling", "remove"),
        ),
    )


blueprints: list[chalice.app.Blueprint] = [template_manager_api]
