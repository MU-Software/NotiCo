# https://docs.nhncloud.com/ko/Notification/KakaoTalk%20Bizmessage/ko/alimtalk-api-guide/
import datetime
import functools
import logging
import typing
import urllib.parse

import chalicelib.config as config_module
import chalicelib.util.decorator_util as decorator_util
import httpx
import pydantic

logger = logging.getLogger(__name__)

# WL: 웹 링크, AL: 앱 링크, BK: 봇 키워드, BC: 상담톡 전환, BT: 봇 전환, BF: 비지니스폼
ActionType = typing.Literal["WL", "AL", "BK", "BC", "BT", "BF"]


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
    linkMo: pydantic.AnyUrl | str | None = pydantic.Field(max_length=500, default=None)
    linkPc: pydantic.AnyUrl | str | None = pydantic.Field(max_length=500, default=None)
    schemeIos: pydantic.AnyUrl | str | None = pydantic.Field(max_length=500, default=None)
    schemeAndroid: pydantic.AnyUrl | str | None = pydantic.Field(max_length=500, default=None)


class RawMsgRecipientAction(RecepientAction, RepresentLink, pydantic.BaseModel):
    type: ActionType
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


class TemplateAction(RepresentLink, pydantic.BaseModel):
    ordering: int
    type: ActionType
    name: str
    bizFormId: int | None = None


class TemplateButton(TemplateAction, pydantic.BaseModel):
    pluginId: str | None = None


class TemplateComment(pydantic.BaseModel):
    class Attachment(pydantic.BaseModel):
        originalFileName: str
        filePath: str

    id: int
    content: str | None = None
    userName: str
    createdAt: datetime.datetime
    attachment: list[Attachment]
    status: str


class Template(pydantic.BaseModel):
    plusFriendId: str
    plusFriendType: typing.Literal["NORMAL", "GROUP"]
    senderKey: str
    templateCode: str
    kakaoTemplateCode: str
    templateName: str
    # 템플릿 메시지 유형(BA: 기본형, EX: 부가 정보형, AD: 채널 추가형, MI: 복합형)
    templateMessageType: typing.Literal["BA", "EX", "AD", "MI"]
    templateEmphasizeType: typing.Literal["NONE", "TEXT", "IMAGE"]
    templateContent: str
    templateExtra: str | None = None
    templateAd: str | None = None
    templateTitle: str | None = None
    templateSubtitle: str | None = None
    templateHeader: str | None = None
    templateItem: TemplateItem | None = None
    templateItemHighlight: TemplateItemHighlight | None = None
    templateRepresentLink: RepresentLink | None = None
    templateImageName: str | None = None
    templateImageUrl: pydantic.HttpUrl | None = None
    buttons: list[TemplateButton]
    quickReplies: list[TemplateAction]
    comments: list[TemplateComment]
    # 템플릿 상태 코드(TSC01: 요청, TSC02: 검수 중, TSC03: 승인, TSC04: 반려)
    status: typing.Literal["TSC01", "TSC02", "TSC03", "TSC04"]
    statusName: str
    securityFlag: bool
    categoryCode: str
    createDate: datetime.datetime
    updateDate: datetime.datetime


class ToastAlimtalkResponseHeader(pydantic.BaseModel):
    resultCode: int
    resultMessage: str
    isSuccessful: bool


class MsgSendResponse(pydantic.BaseModel):
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

    header: ToastAlimtalkResponseHeader
    message: Message


class TemplateCategoriesResponse(pydantic.BaseModel):
    class TemplateCategory(pydantic.BaseModel):
        class TemplateSubCategory(pydantic.BaseModel):
            code: str
            name: str
            groupName: str
            inclusion: str
            exclusion: str

        name: str
        subCategories: list[TemplateSubCategory]

    header: ToastAlimtalkResponseHeader
    categories: list[TemplateCategory]


class TemplateListQueryRequest(pydantic.BaseModel):
    templateCode: str | None = None
    templateName: str | None = None
    templateStatus: str | None = None
    pageNum: int = 1
    pageSize: int = pydantic.Field(ge=1, le=1000, default=1000)


class TemplateListResponse(pydantic.BaseModel):
    class TemplateList(pydantic.BaseModel):
        templates: list[Template]
        totalCount: int

    header: ToastAlimtalkResponseHeader
    templateListResponse: TemplateList


class TemplateDeletionResponse(pydantic.BaseModel):
    header: ToastAlimtalkResponseHeader


class ToastAlimTalkError(Exception):
    pass


class ToastAlimTalkClient(pydantic.BaseModel):
    exc_cls: type[Exception] = ToastAlimTalkError

    @functools.cached_property
    def config(self) -> config_module.ToastConfig:
        return config_module.config.toast

    @functools.cached_property
    def session(self) -> httpx.Client:
        if not config_module.config.toast.is_configured():
            raise ToastAlimTalkError("Toast configuration is not set up properly.")

        return config_module.config.toast.get_session("alimtalk")

    @decorator_util.retry
    def send_alimtalk(self, payload: MsgSendRequest | RawMsgSendRequest) -> MsgSendResponse:
        url = "/messages" if payload.__class__ == MsgSendRequest else "/raw-messages"
        response = self.session.post(url=url, json=payload.model_dump(mode="json")).raise_for_status()
        return MsgSendResponse.model_validate_json(response.read())

    @decorator_util.retry
    def get_template_categories(self) -> TemplateCategoriesResponse:
        url = "/template/categories"
        return TemplateCategoriesResponse.model_validate_json(self.session.get(url=url).raise_for_status().read())

    @decorator_util.retry
    def get_template_list(self, query_params: TemplateListQueryRequest | None = None) -> TemplateListResponse:
        query_str = urllib.parse.urlencode((query_params or TemplateListQueryRequest()).model_dump(exclude_none=True))
        url = f"/senders/{self.config.sender_key.get_secret_value()}/templates?{query_str}"
        return TemplateListResponse.model_validate_json(self.session.get(url=url).raise_for_status().read())

    @decorator_util.retry
    def delete_template(self, template_code: str) -> TemplateDeletionResponse:
        url = f"/senders/{self.config.sender_key.get_secret_value()}/templates/{template_code}"
        return TemplateDeletionResponse.model_validate_json(self.session.delete(url=url).raise_for_status().read())
