import chalicelib.aws_resource as aws_resource
import chalicelib.template_manager.__interface__ as template_mgr_interface
import pydantic


class EmailTemplateManager(template_mgr_interface.S3ResourceTemplateManager):
    class TemplateStructure(pydantic.BaseModel):
        from_: pydantic.EmailStr
        title: str
        body: str

    template_structure_cls = TemplateStructure
    resource = aws_resource.S3ResourcePath.email_template


email_template_manager = EmailTemplateManager()
template_manager_patterns: dict[str, template_mgr_interface.TemplateManagerInterface] = {
    "email": email_template_manager,
}
