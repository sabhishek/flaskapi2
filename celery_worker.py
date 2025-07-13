from celery import Celery

from app import create_app
from config import ProductionConfig

# Build the Flask application using the production configuration.
flask_app = create_app(config_class=ProductionConfig)

# Instantiate Celery and configure it from the Flask app's settings.
celery = Celery(
    flask_app.import_name,
    broker=flask_app.config["CELERY_BROKER_URL"],
    backend=flask_app.config["CELERY_RESULT_BACKEND"],
)
celery.conf.update(flask_app.config)


class FlaskTask(celery.Task):
    """Ensure each Celery task runs inside the Flask application context."""

    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)


# Tell Celery to use the custom Context Task base class.
celery.Task = FlaskTask


# Optional: import task modules here so Celery can discover them automatically.
# from api import tasks  # noqa: E402,F401
