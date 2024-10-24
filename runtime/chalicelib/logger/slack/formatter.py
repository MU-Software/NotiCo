import json
import logging
import traceback
import types
import typing

import chalicelib.logger.slack.block as block

ExcInfoType: typing.TypeAlias = tuple[type[BaseException] | None, BaseException | None, types.TracebackType | None]

DEFAULT_SLACK_LOG_FORMAT = "[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(levelno)s\t%(message)s\n"
DEFAULT_SLACK_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


class SlackJsonFormatter(logging.Formatter):
    """
    SlackJsonFormatter formats log records as JSON strings for Slack BlockKit.
    example:
    >>> logger.info("This is a log message", extra={"data": {"key": "value"}})
    {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": ":pencil: 로그[INFO]", "emoji": true}},
            {"type": "section", "text": {"type": "plain_text", "text": "This is a log message", "emoji": true}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Timestamp*\n```2024-07-20T21:24:20.296Z```"},
                    {"type": "mrkdwn", "text": "*AWS Request ID*\n```00000000-0000-0000-0000-000000000000```"}
                ]
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": "*key1*\n```\"value1\"```"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*key2*\n```\"value2\"```"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*Traceback<Exception>*\n```...```"}}
        ]
    }
    """

    def __init__(
        self,
        fmt: str = DEFAULT_SLACK_LOG_FORMAT,
        datefmt: str = DEFAULT_SLACK_DATE_FORMAT,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt, **kwargs)

    @staticmethod
    def _default_json_dumps(obj: object, **kwargs: typing.Any) -> str:
        return json.dumps(
            obj=obj,
            skipkeys=True,
            ensure_ascii=False,
            default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o),
            **kwargs,
        )

    def formatException(self, exc_info: ExcInfoType) -> block.SlackCodeChildBlock:
        exc_type, exc_value, _ = exc_info
        return block.SlackSectionParentBlock(
            text=block.SlackCodeChildBlock(
                title=f"Traceback<{exc_type.__name__}>",
                text="\n".join(traceback.format_exception(exc_value)),
            )
        )

    def format(  # type: ignore[override]
        self, record: logging.LogRecord
    ) -> list[dict[str, str | dict[str, str | bool]]]:
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        aws_request_id = getattr(record, "aws_request_id", "00000000-0000-0000-0000-000000000000")
        header_text = (
            f":pencil: 로그 [{record.levelname}]"
            if record.levelname != "ERROR"
            else f":rotating_light: 에러 발생! [{record.levelname}]"
        )
        time_text = "%(asctime)s.%(msecs)dZ" % dict(asctime=record.asctime, msecs=record.msecs)

        slack_block = block.SlackBlocks(
            blocks=[
                block.SlackHeaderParentBlock(text=block.SlackPlainTextChildBlock(text=header_text)),
                block.SlackSectionParentBlock(text=block.SlackPlainTextChildBlock(text=record.message)),
                block.SlackSectionParentBlock(
                    fields=[
                        block.SlackCodeChildBlock(title="Timestamp", text=time_text),
                        block.SlackCodeChildBlock(title="AWS Request ID", text=aws_request_id),
                    ],
                ),
            ]
        )
        if extra_data := record.__dict__.get("data"):
            for key, value in extra_data.items():
                slack_block.blocks.append(
                    block.SlackSectionParentBlock(
                        text=block.SlackCodeChildBlock(
                            title=key,
                            text=(
                                value if isinstance(value, (str, int, float, bool)) else self._default_json_dumps(value)
                            ),
                        )
                    )
                )
        if record.exc_info:
            slack_block.blocks.append(self.formatException(record.exc_info))

        return slack_block.to_dict()["blocks"]
