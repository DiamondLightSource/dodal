from logging import INFO, WARNING
from unittest.mock import MagicMock, patch

import pytest

from dodal.common.alerting import get_alerting_service, set_alerting_service
from dodal.common.alerting.log_based_service import LoggingAlertService


def test_default_alerting_service_exists():
    assert isinstance(get_alerting_service(), LoggingAlertService)


@pytest.mark.parametrize("level", [WARNING, INFO])
@patch("dodal.common.alerting.log_based_service.LOGGER")
def test_logging_alerting_service_raises_a_log_message(mock_logger: MagicMock, level):
    set_alerting_service(LoggingAlertService(level))
    get_alerting_service().raise_alert("Test summary", "Test message")

    mock_logger.log.assert_called_once_with(
        level,
        "***ALERT*** summary=Test summary content=Test message",
        extra={"alert_summary": "Test summary", "alert_content": "Test message"},
    )
