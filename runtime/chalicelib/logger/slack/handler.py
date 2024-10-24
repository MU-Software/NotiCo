import json
import logging
import logging.handlers


class SlackHandler(logging.handlers.HTTPHandler):
    channel: str = ""
    token: str = ""

    def __init__(self, channel: str, token: str) -> None:
        super().__init__(host="slack.com", url="/api/chat.postMessage", method="POST", secure=True)
        self.channel = channel
        self.token = token

    def mapLogRecord(self, record: logging.LogRecord) -> dict[str, str]:
        return {
            "text": "NotiCo Logging",
            "channel": self.channel,
            "blocks": self.formatter.format(record),
        }

    def emit(self, record: logging.LogRecord) -> None:
        """From the logging.handlers.HTTPHandler.emit, but with some modifications to send a message to Slack."""
        try:
            connection = self.getConnection(self.host, self.secure)
            connection.request(
                method=self.method,
                url=self.url,
                body=json.dumps(self.mapLogRecord(record)).encode("utf-8"),
                headers={"Content-type": "application/json", "Authorization": f"Bearer {self.token}"},
            )
            connection.getresponse()
        except Exception:
            self.handleError(record)
