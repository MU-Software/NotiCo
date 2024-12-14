import chalicelib.aws_resource as aws_resource
import chalicelib.template_manager.__interface__ as template_mgr_interface
import pydantic


class AWSSESTemplateManager(template_mgr_interface.S3ResourceTemplateManager):
    class TemplateStructure(pydantic.BaseModel):
        from_: pydantic.EmailStr
        title: str
        body: str

    service_name = "aws_ses"
    template_structure_cls = TemplateStructure
    resource = aws_resource.S3ResourcePath.email_template


aws_ses_template_manager = AWSSESTemplateManager()
template_managers = [aws_ses_template_manager]
