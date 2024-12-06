from __future__ import annotations

import dataclasses
import functools
import json
import typing

import botocore.exceptions
import chalicelib.aws_resource as aws_resource
import chalicelib.template_manager.__interface__ as template_mgr_interface
import chalicelib.util.type_util as type_util
import jinja2
import jinja2.meta
import jinja2.nodes
import pydantic


class TemplateInformation(pydantic.BaseModel):
    code: str
    template: type_util.TemplateType
    template_variable_start_end_string: tuple[str, str]

    @pydantic.computed_field  # type: ignore[misc]
    @property
    def template_variables(self) -> set[str]:
        # From https://stackoverflow.com/a/77363330
        template = jinja2.Environment(
            autoescape=True,
            variable_start_string=self.template_variable_start_end_string[0],
            variable_end_string=self.template_variable_start_end_string[1],
        ).parse(source=json.dumps(self.template, ensure_ascii=False))
        return jinja2.meta.find_undeclared_variables(ast=template)


class TemplateManagerInterface(typing.Protocol):
    template_structure_cls: typing.ClassVar[type[pydantic.BaseModel]]
    template_variable_start_end_string: typing.ClassVar[tuple[str, str]] = ("{{", "}}")

    @property
    def initialized(self) -> bool: ...

    def check_template_valid(self, template_data: type_util.TemplateType) -> bool:
        return bool(self.template_structure_cls.model_validate(template_data))

    def list(self) -> list[TemplateInformation]: ...

    def retrieve(self, code: str) -> TemplateInformation | None: ...

    def create(self, code: str, template_data: type_util.TemplateType) -> TemplateInformation: ...

    def update(self, code: str, template_data: type_util.TemplateType) -> TemplateInformation: ...

    def delete(self, code: str) -> None: ...

    def render(self, code: str, context: type_util.ContextType) -> type_util.TemplateType: ...


@dataclasses.dataclass
class S3ResourceTemplateManager(template_mgr_interface.TemplateManagerInterface):
    resource: typing.ClassVar[aws_resource.S3ResourcePath]

    @property
    def initialized(self) -> bool:
        return True

    def list(self) -> list[template_mgr_interface.TemplateInformation]:
        return [self.retrieve(code=f.split(sep=".")[0]) for f in self.resource.list_objects(filter_by_extension=True)]

    @functools.lru_cache  # noqa: B019
    def retrieve(self, code: str) -> template_mgr_interface.TemplateInformation | None:
        try:
            template_body: str = self.resource.download(code=code).decode(encoding="utf-8")
            return template_mgr_interface.TemplateInformation(
                code=code,
                template=template_body,
                template_variable_start_end_string=self.template_variable_start_end_string,
            )
        except botocore.exceptions.ClientError:
            return None

    def create(self, code: str, template_data: type_util.TemplateType) -> template_mgr_interface.TemplateInformation:
        self.check_template_valid(template_data=template_data)
        self.resource.upload(code=code, content=template_data)
        return template_mgr_interface.TemplateInformation(
            code=code,
            template=template_data,
            template_variable_start_end_string=self.template_variable_start_end_string,
        )

    def update(self, code: str, template_data: type_util.TemplateType) -> template_mgr_interface.TemplateInformation:
        return self.create(code=code, template_data=template_data)

    def delete(self, code: str) -> None:
        self.resource.delete(code=code)

    def render(self, code: str, context: type_util.ContextType) -> type_util.TemplateType:
        return json.loads(jinja2.Template(source=json.dumps(obj=self.retrieve(code=code).template)).render(context))
