import logging

from dodal.log import LOGGER


class LoggingAlertService:
    """
    Implement an alert service that raises alerts by generating a specially formatted
    log message, that may be intercepted by a logging service such as graylog and
    used to dispatch the alert.
    """

    def __init__(self, level=logging.WARNING):
        """
        Create a new instance of the service
        Args:
            level: The python logging level at which to generate the message
        """
        super().__init__()
        self._level = level

    def raise_alert(self, summary: str, content: str, metadata: dict[str, str]):
        message = f"***ALERT*** summary={summary} content={content}"
        LOGGER.log(
            self._level,
            message,
            extra={"alert_summary": summary, "alert_content": content} | metadata,
        )
