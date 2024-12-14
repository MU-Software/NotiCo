import typing

import chalicelib.config as config_module
import chalicelib.external_api.__interface__ as external_api_interface
import chalicelib.util.decorator_util as decorator_util
import pydantic


class TelegramUser(pydantic.BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None
    added_to_attachment_menu: bool | None = None
    can_join_groups: bool | None = None
    can_read_all_group_messages: bool | None = None
    supports_inline_queries: bool | None = None
    can_connect_to_business: bool | None = None
    has_main_web_app: bool | None = None


class TelegramMessageEntity(pydantic.BaseModel):
    type: typing.Literal[
        "mention",
        "hashtag",
        "cashtag",
        "bot_command",
        "url",
        "email",
        "phone_number",
        "bold",
        "italic",
        "underline",
        "strikethrough",
        "spoiler",
        "blockquote",
        "expandable_blockquote",
        "code",
        "pre",
        "text_link",
        "text_mention",
        "custom_emoji",
    ]
    offset: int
    length: int
    url: pydantic.HttpUrl | None = None
    user: TelegramUser | None = None
    language: str | None = None
    custom_emoji_id: str | None = None

    @pydantic.field_validator("url", mode="after")
    @classmethod
    def validate_url(cls, url: pydantic.HttpUrl | None, values: dict) -> pydantic.HttpUrl | None:
        if url and values["type"] != "text_link":
            raise ValueError("url is only allowed for type 'text_link'")
        if not url and values["type"] == "text_link":
            raise ValueError("url is required for type 'text_link'")
        return url

    @pydantic.field_validator("user", mode="after")
    @classmethod
    def validate_user(cls, user: TelegramUser | None, values: dict) -> TelegramUser | None:
        if user and values["type"] != "text_mention":
            raise ValueError("user is only allowed for type 'text_mention'")
        if not user and values["type"] == "text_mention":
            raise ValueError("user is required for type 'text_mention'")
        return user

    @pydantic.field_validator("language", mode="after")
    @classmethod
    def validate_language(cls, language: str | None, values: dict) -> str | None:
        if language and values["type"] != "pre":
            raise ValueError("language is only allowed for type 'pre'")
        if not language and values["type"] == "pre":
            raise ValueError("language is required for type 'pre'")
        return language

    @pydantic.field_validator("custom_emoji_id", mode="after")
    @classmethod
    def validate_custom_emoji_id(cls, custom_emoji_id: str | None, values: dict) -> str | None:
        if custom_emoji_id and values["type"] != "custom_emoji":
            raise ValueError("custom_emoji_id is only allowed for type 'custom_emoji'")
        if not custom_emoji_id and values["type"] == "custom_emoji":
            raise ValueError("custom_emoji_id is required for type 'custom_emoji'")
        return custom_emoji_id


class TelegramLinkPreviewOptions(pydantic.BaseModel):
    is_disabled: bool | None = None
    url: pydantic.HttpUrl | None = None
    prefer_small_media: bool | None = None
    prefer_large_media: bool | None = None
    show_above_text: bool | None = None


class TelegramReplyParameters(pydantic.BaseModel):
    message_id: int
    chat_id: int | str | None = None
    allow_sending_without_reply: bool | None = None
    quote: str | None = None
    quote_parse_mode: typing.Literal["MarkdownV2", "HTML"] | None = None
    quote_entities: list[TelegramMessageEntity] | None = None
    quote_position: int | None = None


class TelegramWebAppInfo(pydantic.BaseModel):
    url: pydantic.HttpUrl


class TelegramLoginUrl(pydantic.BaseModel):
    url: pydantic.HttpUrl
    forward_text: str | None = None
    bot_username: str | None = None
    request_write_access: bool | None = None


class TelegramSwitchInlineQueryChosenChat(pydantic.BaseModel):
    query: str | None = None
    allow_user_chats: bool | None = None
    allow_bot_chats: bool | None = None
    allow_group_chats: bool | None = None
    allow_channel_chats: bool | None = None


class TelegramCopyTextButton(pydantic.BaseModel):
    text: str


class TelegramCallbackGame(pydantic.BaseModel):
    pass


class TelegramInlineKeyboardButton(pydantic.BaseModel):
    text: str
    url: pydantic.HttpUrl | None = None
    callback_data: str | None = None
    web_app: TelegramWebAppInfo | None = None
    login_url: TelegramLoginUrl | None = None
    switch_inline_query: str | None = None
    switch_inline_query_current_chat: str | None = None
    switch_inline_query_chosen_chat: TelegramSwitchInlineQueryChosenChat | None = None
    copy_text: TelegramCopyTextButton | None = None
    callback_game: TelegramCallbackGame | None = None
    pay: bool | None = None


class TelegramInlineKeyboardMarkup(pydantic.BaseModel):
    inline_keyboard: list[list[TelegramInlineKeyboardButton]]


class TelegramKeyboardButtonRequestUsers(pydantic.BaseModel):
    request_id: int
    user_is_bot: bool | None = None
    user_is_premium: bool | None = None
    max_quantity: int | None = None
    request_name: bool | None = None
    request_username: bool | None = None
    request_photo: bool | None = None


class TelegramChatAdministratorRights(pydantic.BaseModel):
    is_anonymous: bool = False
    can_manage_chat: bool = False
    can_delete_messages: bool = False
    can_manage_video_chats: bool = False
    can_restrict_members: bool = False
    can_promote_members: bool = False
    can_change_info: bool = False
    can_invite_users: bool = False
    can_post_stories: bool = False
    can_edit_stories: bool = False
    can_delete_stories: bool = False
    can_post_messages: bool | None = None
    can_edit_messages: bool | None = None
    can_pin_messages: bool | None = None
    can_manage_topics: bool | None = None


class TelegramKeyboardButtonRequestChat(pydantic.BaseModel):
    request_id: int
    chat_is_channel: bool
    chat_is_forum: bool | None = None
    chat_has_username: bool | None = None
    chat_is_created: bool | None = None
    user_administrator_rights: TelegramChatAdministratorRights | None = None
    bot_administrator_rights: TelegramChatAdministratorRights | None = None
    bot_is_member: bool | None = None
    request_title: bool | None = None
    request_username: bool | None = None
    request_photo: bool | None = None


class TelegramKeyboardButtonPollType(pydantic.BaseModel):
    type: typing.Literal["quiz", "regular"] | None = None


class TelegramKeyboardButton(pydantic.BaseModel):
    text: str
    request_users: TelegramKeyboardButtonRequestUsers | None = None
    request_chat: TelegramKeyboardButtonRequestChat | None = None
    request_contact: bool | None = None
    request_location: bool | None = None
    request_poll: TelegramKeyboardButtonPollType | None = None
    web_app: TelegramWebAppInfo | None = None


class TelegramReplyKeyboardMarkup(pydantic.BaseModel):
    keyboard: list[list[TelegramKeyboardButton]]
    is_persistent: bool | None = None
    resize_keyboard: bool | None = None
    one_time_keyboard: bool | None = None
    input_field_placeholder: str | None = None
    selective: bool | None = None


class TelegramReplyKeyboardRemove(pydantic.BaseModel):
    remove_keyboard: typing.Literal[True] = True
    selective: bool | None = None


class TelegramForceReply(pydantic.BaseModel):
    force_reply: typing.Literal[True] = True
    input_field_placeholder: str | None = None
    selective: bool | None = None


class TelegramSendMessageRequestPayload(pydantic.BaseModel):
    business_connection_id: str | None = None
    chat_id: int | str
    message_thread_id: int | None = None
    text: str
    parse_mode: typing.Literal["MarkdownV2", "HTML"] | None = None
    entities: list[TelegramMessageEntity] | None = None
    link_preview_options: TelegramLinkPreviewOptions | None = None
    disable_notification: bool | None = None
    protect_content: bool | None = None
    allow_paid_broadcast: bool | None = None
    message_effect_id: str | None = None
    reply_parameters: TelegramReplyParameters | None = None
    reply_markup: (
        TelegramInlineKeyboardMarkup
        | TelegramReplyKeyboardMarkup
        | TelegramReplyKeyboardRemove
        | TelegramForceReply
        | None
    ) = None


class TelegramBotMessagingError(Exception):
    pass


class TelegramBotMessagingClient(external_api_interface.ExternalClientInterface):
    exc_cls = TelegramBotMessagingError
    config = config_module.config.telegram

    @decorator_util.retry
    def send_message(self, payload: TelegramSendMessageRequestPayload) -> str:
        response = self.session.post(url="/sendMessage", json=payload.model_dump(mode="json")).raise_for_status()
        return typing.cast(dict, typing.cast(dict, response.json()).get("result", {})).get("message_id", "")
