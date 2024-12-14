from __future__ import annotations

import json
import pathlib
import random
import typing

import botocore.exceptions
import chalicelib.aws_resource as aws_resource
import chalicelib.template_manager.__interface__ as template_mgr_interface
import chalicelib.util.jinja_util as jinja_util
import chalicelib.util.type_util as type_util
import jinja2
import jinja2.meta
import jinja2.nodes
import pydantic

TEMPLATE_HTML_PATH = pathlib.Path(__file__).parent / "preview"
TemplateType = dict[str, type_util.AllowedBasicValueTypes]
NotDefinedVariableHandlingType = typing.Literal["random", "show_as_template_var", "remove"]


class TemplateInformation(pydantic.BaseModel):
    template_code: str
    template: TemplateType
    template_variable_start_end_string: tuple[str, str]

    @pydantic.computed_field  # type: ignore[misc]
    @property
    def template_variables(self) -> set[str]:
        return jinja_util.get_template_variables(
            template_str=json.dumps(self.template, ensure_ascii=False),
            template_variable_start_end_string=self.template_variable_start_end_string,
        )


class TemplateManagerInterface:
    service_name: typing.ClassVar[str]
    template_structure_cls: typing.ClassVar[type[pydantic.BaseModel]]
    template_variable_start_end_string: typing.ClassVar[tuple[str, str]] = ("{{", "}}")

    def __init_subclass__(cls, check_classvar_initialized: bool = True) -> None:
        if check_classvar_initialized:
            type_util.check_classvar_initialized(cls, ["service_name", "template_structure_cls"])

    @property
    def initialized(self) -> bool: ...

    def check_template_valid(self, template_data: TemplateType) -> bool:
        return bool(self.template_structure_cls.model_validate(template_data))

    def list(self) -> list[TemplateInformation]: ...

    def retrieve(self, template_code: str) -> TemplateInformation | None: ...

    def create(self, template_code: str, template_data: TemplateType) -> TemplateInformation: ...

    def update(self, template_code: str, template_data: TemplateType) -> TemplateInformation: ...

    def delete(self, template_code: str) -> None: ...

    def render(
        self,
        template_code: str,
        context: type_util.ContextType,
        *,
        not_defined_variable_handling: NotDefinedVariableHandlingType = "random",
    ) -> TemplateType:
        template = self.retrieve(template_code=template_code).template
        template_variables = jinja_util.get_template_variables(
            template_str=json.dumps(template, ensure_ascii=False),
            template_variable_start_end_string=self.template_variable_start_end_string,
        )
        for key in template_variables - context.keys():
            if not_defined_variable_handling == "show_as_template_var":
                start, end = self.template_variable_start_end_string
                context[key] = f"{start} {key} {end}"
            elif not_defined_variable_handling == "random":
                context[key] = f"RandomValue-{random.randint(1000, 9999)}"  # nosec: B311

        return (
            json.loads(
                s=jinja2.Template(
                    source=json.dumps(obj=template, ensure_ascii=False),
                    variable_start_string=self.template_variable_start_end_string[0],
                    variable_end_string=self.template_variable_start_end_string[1],
                ).render(context)
            )
            | context
        )

    def render_html(
        self,
        template_code: str,
        context: type_util.ContextType,
        *,
        not_defined_variable_handling: NotDefinedVariableHandlingType = "random",
    ) -> str:
        template_file = TEMPLATE_HTML_PATH / f"{self.service_name}.html"
        if not template_file.is_file():
            raise FileNotFoundError(f"Template file not found: {template_file}")

        return jinja2.Template(source=template_file.read_text(encoding="utf-8")).render(
            self.render(
                template_code=template_code,
                context=context,
                not_defined_variable_handling=not_defined_variable_handling,
            )
        )


class S3ResourceTemplateManager(
    template_mgr_interface.TemplateManagerInterface,
    check_classvar_initialized=False,
):  # type: ignore[call-arg]
    resource: typing.ClassVar[aws_resource.S3ResourcePath]

    def __init_subclass__(cls) -> None:
        type_util.check_classvar_initialized(cls, ["resource"])
        super().__init_subclass__()

    @property
    def initialized(self) -> bool:
        return True

    def list(self) -> list[template_mgr_interface.TemplateInformation]:
        return [
            self.retrieve(template_code=f.split(sep=".")[0])
            for f in self.resource.list_objects(filter_by_extension=True)
        ]

    def retrieve(self, template_code: str) -> template_mgr_interface.TemplateInformation | None:
        try:
            template_body: str = self.resource.download(template_code=template_code).decode(encoding="utf-8")
            return template_mgr_interface.TemplateInformation(
                template_code=template_code,
                template=json.loads(template_body),
                template_variable_start_end_string=self.template_variable_start_end_string,
            )
        except botocore.exceptions.ClientError:
            return None

    def create(self, template_code: str, template_data: TemplateType) -> template_mgr_interface.TemplateInformation:
        self.check_template_valid(template_data=template_data)
        self.resource.upload(template_code=template_code, content=json.dumps(template_data))
        return template_mgr_interface.TemplateInformation(
            template_code=template_code,
            template=template_data,
            template_variable_start_end_string=self.template_variable_start_end_string,
        )

    def update(self, template_code: str, template_data: TemplateType) -> template_mgr_interface.TemplateInformation:
        return self.create(template_code=template_code, template_data=template_data)

    def delete(self, template_code: str) -> None:
        self.resource.delete(template_code=template_code)
