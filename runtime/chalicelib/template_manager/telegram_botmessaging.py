import chalicelib.aws_resource as aws_resource
import chalicelib.external_api.telegram_botmessaging as telegram_client
import chalicelib.template_manager.__interface__ as template_mgr_interface
import pydantic


class SimplifiedTelegramTemplate(pydantic.BaseModel):
    class Button(pydantic.BaseModel):
        text: str
        url: str

        def to_telegram_button(self) -> telegram_client.TelegramInlineKeyboardButton:
            return telegram_client.TelegramInlineKeyboardButton(text=self.text, url=self.url)

    body: str
    entities: list[telegram_client.TelegramMessageEntity]
    buttons: list[list[Button]]

    def to_send_message_request_payload(self, chat_id: int | str) -> telegram_client.TelegramSendMessageRequestPayload:
        return telegram_client.TelegramSendMessageRequestPayload(
            chat_id=chat_id,
            text=self.body,
            parse_mode="MarkdownV2",
            entities=self.entities or None,
            reply_markup=(
                telegram_client.TelegramInlineKeyboardMarkup(
                    inline_keyboard=[[b.to_telegram_button() for b in bs] for bs in self.buttons]
                )
                if self.buttons
                else None
            ),
            link_preview_options=telegram_client.TelegramLinkPreviewOptions(is_disabled=True),
            protect_content=False,
            disable_notification=False,
            allow_paid_broadcast=False,
        )


class TelegramTemplateManager(template_mgr_interface.S3ResourceTemplateManager):
    service_name = "telegram_botmessaging"
    permission = template_mgr_interface.TemplateManagerPermission()
    template_structure_cls = SimplifiedTelegramTemplate
    resource = aws_resource.S3ResourcePath.telegram_template


telegram_template_manager = TelegramTemplateManager()
template_managers = [telegram_template_manager]
