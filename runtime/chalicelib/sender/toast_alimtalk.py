# https://docs.nhncloud.com/ko/Notification/KakaoTalk%20Bizmessage/ko/alimtalk-api-guide/
import contextlib
import datetime
import functools
import json
import logging
import typing

import chalicelib.config
import chalicelib.util.decorator_util as decorator_util
import httpx
import pydantic

logger = logging.getLogger(__name__)


class RecepientAction(pydantic.BaseModel):
    ordering: int
    chatExtra: str | None = None
    chatEvent: str | None = None
    target: str | None = None


class RecepientButton(RecepientAction, pydantic.BaseModel):
    relayId: str | None = None
    oneClickId: str | None = None
    productId: str | None = None


class MsgSendRequest(pydantic.BaseModel):
    class Recipient(pydantic.BaseModel):
        class ResendParameter(pydantic.BaseModel):
            isResend: bool
            resendType: typing.Literal["SMS", "LMS"] | None = None
            resendTitle: str | None = None
            resendContent: str | None = None
            resendSendNo: str

        recipientNo: str = pydantic.Field(max_length=15)
        resendParameter: ResendParameter | None = None
        recipientGroupingKey: str | None = None

        templateParameter: dict[str, str] | None = None
        buttons: list[RecepientButton] = pydantic.Field(default_factory=list)
        quickReplies: list[RecepientAction] = pydantic.Field(default_factory=list)

    class MessageOption(pydantic.BaseModel):
        price: int | None = None
        currencyType: str | None = None

    senderKey: str = pydantic.Field(max_length=40)
    templateCode: str = pydantic.Field(max_length=20)
    requestDate: pydantic.FutureDate | None = None
    senderGroupingKey: str | None = None
    createUser: str | None = None
    recipientList: list[Recipient] = pydantic.Field(default_factory=list)
    messageOption: MessageOption | None = None
    statsId: str | None = pydantic.Field(max_length=8, default=None)

    @pydantic.field_validator("requestDate", mode="before")
    def validate_request_date(cls, v: datetime.datetime | None) -> datetime.datetime | None:
        if v and v.date() - datetime.date.today() > datetime.timedelta(days=60):
            raise ValueError("The request date should not be more than 60 days in the future.")

        return v

    @pydantic.field_serializer("requestDate", mode="plain", return_type=str)
    def serialize_request_date(v: datetime.datetime | None) -> str | None:
        return v.strftime("%Y-%m-%d %H:%M") if v else None


class TemplateAtom(pydantic.BaseModel):
    title: str
    description: str


class TemplateItemHighlight(TemplateAtom):
    imageUrl: pydantic.HttpUrl


class TemplateItem(pydantic.BaseModel):
    list: list[TemplateAtom]
    summary: TemplateAtom


class RepresentLink(pydantic.BaseModel):
    linkMo: pydantic.HttpUrl | None = pydantic.Field(max_length=500, default=None)
    linkPc: pydantic.HttpUrl | None = pydantic.Field(max_length=500, default=None)
    schemeIos: pydantic.AnyUrl | None = pydantic.Field(max_length=500, default=None)
    schemeAndroid: pydantic.AnyUrl | None = pydantic.Field(max_length=500, default=None)


class RawMsgRecipientAction(RecepientAction, RepresentLink, pydantic.BaseModel):
    # WL: 웹 링크, AL: 앱 링크, BK: 봇 키워드, BC: 상담톡 전환, BT: 봇 전환, BF: 비지니스폼
    type: typing.Literal["WL", "AL", "BK", "BC", "BT", "BF"]
    name: str = pydantic.Field(max_length=14)
    bizFormId: int | None = None


class RawMsgRecepientButton(RawMsgRecipientAction, RecepientButton, pydantic.BaseModel):
    pluginId: str | None = None


class RawMsgSendRequest(MsgSendRequest):
    class Recipient(MsgSendRequest.Recipient):
        templateParameter: None = None
        buttons: list[RawMsgRecepientButton] = pydantic.Field(default_factory=list)
        quickReplies: list[RawMsgRecipientAction] = pydantic.Field(default_factory=list)

        templateTitle: str | None = None
        templateHeader: str | None = None
        templateItem: TemplateItem | None = None
        templateItemHighlight: TemplateItemHighlight | None = None
        templateRepresentLink: RepresentLink | None = None
        content: str = pydantic.Field(max_length=1000)

    recipientList: list[Recipient] = pydantic.Field(default_factory=list)


class MsgSendResponse(pydantic.BaseModel):
    class Header(pydantic.BaseModel):
        resultCode: int
        resultMessage: str
        isSuccessful: bool

    class Message(pydantic.BaseModel):
        class SendResult(pydantic.BaseModel):
            recipientSeq: int
            recipientNo: str
            resultCode: int
            resultMessage: str
            recipientGroupingKey: str | None = None

        requestId: str
        senderGroupingKey: str | None = None
        sendResults: list[SendResult]

    header: Header
    message: Message


class ToastAlimTalkError(Exception):
    pass


class ToastAlimTalkClient(pydantic.BaseModel):
    conf: chalicelib.config.ToastConfig
    payload: MsgSendRequest | RawMsgSendRequest
    exc_cls: type[Exception] = ToastAlimTalkError

    @functools.cached_property
    def session(self) -> httpx.Client:
        if not self.conf.is_configured():
            raise ToastAlimTalkError("Toast configuration is not set up properly.")

        return self.conf.get_session("alimtalk")

    @decorator_util.retry
    def send(self, payload: MsgSendRequest) -> MsgSendResponse | None:
        response = self.session.post(
            url="/messages" if payload.__class__ == MsgSendRequest else "/raw-messages",
            json=self.payload.model_dump(mode="json"),
        ).raise_for_status()
        logger.debug(f"Response :\n{response.content.decode(errors='ignore')}")

        with contextlib.suppress(pydantic.ValidationError, json.JSONDecodeError):
            return MsgSendResponse.model_validate_json(response.content)
        return None
