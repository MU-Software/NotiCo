import functools
import typing

import chalicelib.config as config_module
import chalicelib.external_api.toast_alimtalk as toast_alimtalk_client
import chalicelib.send_manager.__interface__ as sendmgr_interface
import chalicelib.template_manager.toast_alimtalk as toast_alimtalk_template_mgr


class ToastAlimtalkSendRequest(sendmgr_interface.BaseSendRequest):
    def as_request_payload(self) -> toast_alimtalk_client.MsgSendRequest:
        return toast_alimtalk_client.MsgSendRequest(
            senderKey=config_module.config.toast.sender_key.get_secret_value(),
            templateCode=self.template_code,
            recipientList=[
                toast_alimtalk_client.MsgSendRequest.Recipient(
                    recipientNo=send_to,
                    templateParameter=personalized_data,
                )
                for send_to, personalized_data in self.personalized_context.items()
            ],
        )


class ToastAlimtalkSendManager(
    sendmgr_interface.SendManagerInterface[
        ToastAlimtalkSendRequest,
        sendmgr_interface.BaseSendRawRequest,
        toast_alimtalk_template_mgr.ToastAlimtalkTemplateManager,
    ]
):
    CAN_SEND_RAW_MESSAGE: bool = True

    @property
    def initialized(self) -> bool:
        return config_module.config.toast.is_configured()

    @property
    def template_manager(self) -> toast_alimtalk_template_mgr.ToastAlimtalkTemplateManager:
        return toast_alimtalk_template_mgr.toast_alimtalk_template_manager

    @functools.cached_property
    def client(self) -> toast_alimtalk_client.ToastAlimTalkClient:
        return toast_alimtalk_client.ToastAlimTalkClient()

    def send(self, request: ToastAlimtalkSendRequest) -> dict[str, str]:
        request_payload = request.as_request_payload()
        return {r.recipientNo: r.resultCode for r in self.client.send_alimtalk(request_payload).message.sendResults}

    def send_raw(self, request: sendmgr_interface.BaseSendRawRequest) -> typing.NoReturn:
        raise NotImplementedError("Toast 알림톡은 Raw 메시지를 보낼 수 없습니다.")


toast_alimtalk_send_manager = ToastAlimtalkSendManager()
send_manager_patterns: dict[str, sendmgr_interface.SendManagerInterface] = {
    "toast_alimtalk": toast_alimtalk_send_manager,
}
