import chalicelib.aws_resource as aws_resource
import chalicelib.template_manager.__interface__ as template_mgr_interface
import pydantic


class FirebaseTemplateManager(template_mgr_interface.S3ResourceTemplateManager):
    class TemplateStructure(pydantic.BaseModel):
        title: str
        body: str

    template_structure_cls = TemplateStructure
    resource = aws_resource.S3ResourcePath.firebase_template


firebase_cloudmessaging_template_manager = FirebaseTemplateManager()
template_manager_patterns: dict[str, template_mgr_interface.TemplateManagerInterface] = {
    "firebase_cloudmessaging": firebase_cloudmessaging_template_manager,
}
