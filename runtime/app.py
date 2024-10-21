import chalice.app
import chalicelib.config
import chalicelib.route
import chalicelib.worker

config = chalicelib.config.get_config()
app = chalice.app.Chalice(app_name="notico")
chalicelib.route.register_route(app)
chalicelib.worker.register_worker(app, queue=config.infra.queue_name)
