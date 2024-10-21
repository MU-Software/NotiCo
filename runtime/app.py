import json
import logging
import typing

import chalice.app
import chalicelib.config
import chalicelib.route
import chalicelib.worker

config = chalicelib.config.get_config()
app = chalice.app.Chalice(app_name="notico")
app.log.setLevel(logging.DEBUG)

chalicelib.route.register_route(app)


@app.on_sqs_message(queue=config.infra.queue_name)
def sqs_handler(event: chalice.app.SQSEvent) -> dict[str, typing.Any]:
    try:
        parsed_event = event.to_dict()
        app.log.info(f"event: {parsed_event}")
        result = chalicelib.worker.workers[json.loads(parsed_event["body"])["worker"]](event)
        app.log.info(f"result: {result}")
        return result
    except Exception as e:
        app.log.error(f"Failed to handle event: {parsed_event}", exc_info=e)
        return {"error": "Failed to handle event"}
