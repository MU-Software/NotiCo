from __future__ import annotations

import dataclasses
import functools
import typing

import chalicelib.config as config_module
import chalicelib.external_api.toast_alimtalk as toast_alimtalk_client
import chalicelib.template_manager.__interface__ as template_mgr_interface
import chalicelib.util.type_util as type_util
import jinja2


@dataclasses.dataclass
class ToastAlimtalkTemplateManager(template_mgr_interface.TemplateManagerInterface):
    template_structure_cls = toast_alimtalk_client.Template
    template_variable_start_end_string: typing.ClassVar[tuple[str, str]] = ("#{", "}")

    @property
    def initialized(self) -> bool:
        return config_module.config.toast.is_configured()

    @functools.cached_property
    def client(self) -> toast_alimtalk_client.ToastAlimTalkClient:
        return toast_alimtalk_client.ToastAlimTalkClient()

    def list(self) -> list[template_mgr_interface.TemplateInformation]:
        return [
            template_mgr_interface.TemplateInformation(
                code=t.templateCode,
                template=t.model_dump(mode="json"),
                template_variable_start_end_string=self.template_variable_start_end_string,
            )
            for t in self.client.get_template_list().templateListResponse.templates
            if t.status == "TSC03"
        ]

    def retrieve(self, code: str) -> template_mgr_interface.TemplateInformation | None:
        query_params = toast_alimtalk_client.TemplateListQueryRequest(templateCode=code)
        if t := self.client.get_template_list(query_params=query_params).templateListResponse.templates:
            return template_mgr_interface.TemplateInformation(
                code=t[0].templateCode,
                template=t[0].model_dump(mode="json"),
                template_variable_start_end_string=self.template_variable_start_end_string,
            )
        return None

    def create(self, code: str, template_data: str) -> template_mgr_interface.TemplateInformation:
        raise NotImplementedError("Toast 콘솔에서 직접 템플릿을 생성해주세요.")

    def update(self, code: str, template_data: str) -> None:
        raise NotImplementedError("Toast 콘솔에서 직접 템플릿을 수정해주세요.")

    def delete(self, code: str) -> None:
        raise NotImplementedError("Toast 콘솔에서 직접 템플릿을 삭제해주세요.")

    def render(self, code: str, context: type_util.ContextType) -> str:
        return jinja2.Template(source=self.retrieve(code=code).template).render(context)


toast_alimtalk_template_manager = ToastAlimtalkTemplateManager()
template_manager_patterns: dict[str, template_mgr_interface.TemplateManagerInterface] = {
    "toast_alimtalk": toast_alimtalk_template_manager,
}
