import logging
import json
import sys
from datetime import datetime, timezone
from app.core.config import settings

class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter for cloud logging collectors (Datadog, CloudWatch, Render).
    """
    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "line": record.lineno
        }
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_object)


def setup_logging():
    """
    Initializes structured JSON logging and optional Sentry exception tracking.
    """
    logger = logging.getLogger("keepsong")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    # Initialize Sentry monitoring if SENTRY_DSN is configured
    sentry_dsn = getattr(settings, "SENTRY_DSN", None)
    if sentry_dsn and sentry_dsn.startswith("http"):
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration

            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FastApiIntegration(), SqlAlchemyIntegration()],
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                environment=getattr(settings, "ENVIRONMENT", "production")
            )
            logger.info("Sentry monitoring successfully initialized.")
        except Exception as e:
            logger.warning(f"Failed to initialize Sentry SDK: {str(e)}")

    return logger

logger = setup_logging()
