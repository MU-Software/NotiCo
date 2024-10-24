import dataclasses
import logging

import chalicelib.logger.slack.formatter as slack_formatter
import chalicelib.logger.slack.handler as slack_handler


@dataclasses.dataclass
class SlackLogger:
    channel: str
    token: str
    level: int = logging.DEBUG
    logger: logging.Logger = dataclasses.field(default_factory=lambda: logging.getLogger("slack"))

    def __post_init__(self) -> None:
        handler = slack_handler.SlackHandler(channel=self.channel, token=self.token)
        handler.setFormatter(slack_formatter.SlackJsonFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(self.level)
