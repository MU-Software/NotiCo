import traceback

import botocore.exceptions
import chalicelib.aws_resource as aws_resource_module
import chalicelib.send_manager.__interface__ as sendmgr_interface
import chalicelib.template_manager.aws_ses as aws_ses_template_mgr


class AWSSESSendRawRequest(sendmgr_interface.BaseSendRawRequest):
    personalized_content: dict[str, aws_ses_template_mgr.EmailTemplateManager.TemplateStructure]


class AWSSESSendManager(
    sendmgr_interface.SendManagerInterface[
        sendmgr_interface.BaseSendRequest, AWSSESSendRawRequest, aws_ses_template_mgr.EmailTemplateManager
    ]
):
    CAN_SEND_RAW_MESSAGE: bool = True

    @property
    def initialized(self) -> bool:
        return True

    @property
    def template_manager(self) -> aws_ses_template_mgr.EmailTemplateManager:
        return aws_ses_template_mgr.email_template_manager

    def _send_email(self, from_: str, to_: str, title: str, body: str) -> str:
        try:
            return aws_resource_module.ses_client.send_email(
                Source=from_,
                # Because if you send it to multiple people at once,
                # the e-mail addresses of the people you send with might be exposed to each other.
                # So, we send it one by one.
                Destination={"ToAddresses": [to_]},
                Message={
                    "Subject": {"Charset": "UTF-8", "Data": title},
                    "Body": {"Html": {"Charset": "UTF-8", "Data": body}},
                },
            )["MessageId"]
        except Exception as e:
            err_tb = "\n".join(traceback.format_exception(e))
            if isinstance(e, botocore.exceptions.HTTPClientError):
                return e.response.get("Error", {}).get("Message", err_tb)
            return err_tb

    def send(self, request: sendmgr_interface.SendRequestType) -> dict[str, str]:
        result: dict[str, str] = {}

        for receiver, personalized_context in request.personalized_context.items():
            context = request.shared_context | personalized_context
            render_result = self.template_manager.render(code=request.template_code, context=context)
            result[receiver] = self._send_email(
                from_=render_result["from_address"],
                to_=receiver,
                title=render_result["title"],
                body=render_result["body"],
            )

        return result

    def send_raw(self, request: AWSSESSendRawRequest) -> dict[str, str | None]:
        content_set = request.personalized_content.items()
        return {r: self._send_email(from_=c.from_, to_=r, title=c.title, body=c.body) for r, c in content_set}


aws_ses_send_manager = AWSSESSendManager()
send_manager_patterns: dict[str, sendmgr_interface.SendManagerInterface] = {
    "aws_ses": aws_ses_send_manager,
}
