import logging

import chalice.app
import chalicelib.config as config_module
import chalicelib.logger.slack as slack_logger
import chalicelib.route
import chalicelib.worker

config = config_module.config
app = chalice.app.Chalice(app_name="notico")
app.log.setLevel(logging.INFO)

if config.slack.is_configured():
    slack_logger.SlackLogger(channel=config.slack.channel, token=config.slack.token.get_secret_value(), logger=app.log)
else:
    app.log.setLevel(logging.DEBUG)
    app.log.warning("Slack logger is not configured")

chalicelib.route.register_blueprints(app)
chalicelib.worker.register_worker(app)
