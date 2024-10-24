import dataclasses
import typing


@dataclasses.dataclass
class SlackChildBlock:
    text: str
    block_type: typing.Literal["plain_text", "mrkdwn"] = "mrkdwn"

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "type": self.block_type,
            "text": self.text,
        } | ({"emoji": True} if self.block_type == "plain_text" else {})


@dataclasses.dataclass
class SlackPlainTextChildBlock(SlackChildBlock):
    block_type: typing.Literal["plain_text"] = "plain_text"


@dataclasses.dataclass
class SlackMarkDownChildBlock(SlackChildBlock):
    block_type: typing.Literal["mrkdwn"] = "mrkdwn"


@dataclasses.dataclass
class SlackCodeChildBlock(SlackMarkDownChildBlock):
    title: str = ""

    def __post_init__(self) -> None:
        code_title = f"*{self.title}*\n" if self.title else ""
        self.text = f"{code_title}```{self.text}```"


@dataclasses.dataclass
class SlackParentBlock:
    block_type: str
    text: SlackChildBlock | None = None
    fields: list[SlackChildBlock] | None = None

    def __post_init__(self) -> None:
        if not (self.text or self.fields):
            raise ValueError("At least one of text or fields must be set!")

    def to_dict(self) -> dict[str, str | dict[str, str | bool] | list[dict[str, str | bool]]]:
        result: dict[str, str | dict[str, str | bool] | list[dict[str, str | bool]]] = {
            "type": self.block_type,
            "text": self.text.to_dict() if self.text else None,
            "fields": [f.to_dict() for f in self.fields] if self.fields else None,
        }
        return {k: v for k, v in result.items() if k and v}


@dataclasses.dataclass
class SlackHeaderParentBlock(SlackParentBlock):
    block_type: str = "header"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.fields:
            raise ValueError("header block only allows text, not fields!")
        if self.text.block_type != "plain_text":
            raise ValueError("header block only allows plain_text text block!")


@dataclasses.dataclass
class SlackSectionParentBlock(SlackParentBlock):
    block_type: str = "section"


@dataclasses.dataclass
class SlackBlocks:
    blocks: list[SlackParentBlock]

    def to_dict(self) -> dict[str, list[dict[str, str | dict[str, str | bool] | list[dict[str, str | bool]]]]]:
        return {"blocks": [b.to_dict() for b in self.blocks]}
