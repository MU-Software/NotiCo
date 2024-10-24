import json
import logging
import typing

import chalice.app
import chalicelib.config
import chalicelib.logger.slack as slack_logger
import chalicelib.route
import chalicelib.worker

if typing.TYPE_CHECKING:
    import mypy_boto3_sqs.type_defs

    SQSEventType = typing.TypedDict("SQSEventType", {"Records": list["mypy_boto3_sqs.type_defs.MessageTypeDef"]})
else:
    SQSEventType = dict[str, typing.Any]


config = chalicelib.config.get_config()
app = chalice.app.Chalice(app_name="notico")

if config.slack.is_configured():
    slack_logger.SlackLogger(channel=config.slack.channel, token=config.slack.token.get_secret_value(), logger=app.log)
else:
    app.log.setLevel(logging.DEBUG)
    app.log.warning("Slack logger is not configured")

chalicelib.route.register_route(app)


@app.on_sqs_message(queue=config.infra.queue_name)
def sqs_handler(event: chalice.app.SQSEvent) -> list[dict[str, typing.Any]]:
    parsed_event: SQSEventType = event.to_dict()
    app.log.info(f"{parsed_event=}")

    results: list[dict[str, typing.Any]] = []
    for record in parsed_event["Records"]:
        try:
            result = chalicelib.worker.workers[json.loads(record["body"])["worker"]](record)
            results.append(result)
        except Exception as e:
            app.log.error(f"Failed to handle event: {record}", exc_info=e)
            results.append({"error": "Failed to handle event"})

    app.log.info(f"{results=}")
    return results
