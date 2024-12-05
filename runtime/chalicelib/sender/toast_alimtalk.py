import chalicelib.config as config_module
import chalicelib.external_api.toast_alimtalk as toast_alimtalk_client
import chalicelib.sender.__interface__ as sender_interface


class ToastAlimTalkSendRequest(sender_interface.NotificationSendRequest):
    def to_toast_alimtalk_client(self) -> toast_alimtalk_client.MsgSendResponse:
        return toast_alimtalk_client.ToastAlimTalkClient().send_alimtalk(
            toast_alimtalk_client.MsgSendRequest(
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
        )


def send_notification(request: ToastAlimTalkSendRequest | dict) -> dict | None:
    return (
        (ToastAlimTalkSendRequest.model_validate(request) if isinstance(request, dict) else request)
        .to_toast_alimtalk_client()
        .model_dump(mode="json")
    )


sender_patterns = {
    "toast_alimtalk": send_notification,
}
