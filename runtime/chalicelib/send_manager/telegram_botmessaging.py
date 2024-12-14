import logging
import traceback

import chalicelib.config as config_module
import chalicelib.external_api.telegram_botmessaging as telegram_client
import chalicelib.send_manager.__interface__ as sendmgr_interface
import chalicelib.template_manager.telegram_botmessaging as telegram_template_mgr
import httpx

logger = logging.getLogger(__name__)


class TelegramBotMessagingSender(sendmgr_interface.SendManagerInterface):
    template_manager = telegram_template_mgr.telegram_template_manager
    client = telegram_client.TelegramBotMessagingClient()

    service_name = "telegram_botmessaging"
    initialized = config_module.config.telegram.is_configured()

    def _send_message(self, chat_id: int | str, render_result: dict[str, str]) -> str:
        try:
            return self.client.send_message(
                payload=(
                    telegram_template_mgr.SimplifiedTelegramTemplate.model_validate(render_result)
                    .to_send_message_request_payload(chat_id=chat_id)
                    .model_dump(mode="json")
                )
            )
        except Exception as e:
            return e.response.text if isinstance(e, httpx.HTTPStatusError) else "".join(traceback.format_exception(e))

    def send(self, request: sendmgr_interface.SendRequest) -> dict[str, str]:
        return {
            chat_id: self._send_message(
                chat_id=chat_id,
                render_result=self.template_manager.render(
                    template_code=request.template_code,
                    context=request.shared_context | personalized_context,
                ),
            )
            for chat_id, personalized_context in request.personalized_context.items()
        }
