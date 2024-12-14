import chalicelib.config as config_module
import chalicelib.external_api.toast_alimtalk as toast_alimtalk_client
import chalicelib.send_manager.__interface__ as sendmgr_interface
import chalicelib.template_manager.toast_alimtalk as toast_alimtalk_template_mgr


def _send_request_to_toast_request_payload(req: sendmgr_interface.SendRequest) -> toast_alimtalk_client.MsgSendRequest:
    return toast_alimtalk_client.MsgSendRequest(
        senderKey=config_module.config.toast.sender_key.get_secret_value(),
        templateCode=req.template_code,
        recipientList=[
            toast_alimtalk_client.MsgSendRequest.Recipient(
                recipientNo=send_to,
                templateParameter=personalized_data,
            )
            for send_to, personalized_data in req.personalized_context.items()
        ],
    )


class ToastAlimtalkSendManager(sendmgr_interface.SendManagerInterface):
    template_manager = toast_alimtalk_template_mgr.toast_alimtalk_template_manager
    send_request_cls: sendmgr_interface.SendRequest
    client = toast_alimtalk_client.ToastAlimTalkClient()

    service_name = "toast_alimtalk"
    initialized = config_module.config.toast.is_configured()

    def send(self, request: sendmgr_interface.SendRequest) -> dict[str, str]:
        request_payload = _send_request_to_toast_request_payload(request)
        return {r.recipientNo: r.resultCode for r in self.client.send_alimtalk(request_payload).message.sendResults}


toast_alimtalk_send_manager = ToastAlimtalkSendManager()
send_managers = [toast_alimtalk_send_manager]
