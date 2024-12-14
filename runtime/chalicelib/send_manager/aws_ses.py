import traceback

import botocore.exceptions
import chalicelib.aws_resource as aws_resource_module
import chalicelib.send_manager.__interface__ as sendmgr_interface
import chalicelib.template_manager.aws_ses as aws_ses_template_mgr


class AWSSESSendManager(sendmgr_interface.SendManagerInterface):
    template_manager = aws_ses_template_mgr.aws_ses_template_manager

    service_name = "aws_ses"
    initialized = True

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

    def send(self, request: sendmgr_interface.SendRequest) -> dict[str, str]:
        result: dict[str, str] = {}

        for receiver, personalized_context in request.personalized_context.items():
            context = request.shared_context | personalized_context
            render_result = self.template_manager.render(template_code=request.template_code, context=context)
            result[receiver] = self._send_email(
                from_=render_result["from_"],
                to_=receiver,
                title=render_result["title"],
                body=render_result["body"],
            )

        return result


aws_ses_send_manager = AWSSESSendManager()
send_managers = [aws_ses_send_manager]
