import logging

import pytest

from dodal.common.alerting.log_based_service import LoggingAlertService
from dodal.log import get_graylog_configuration, set_up_graylog_handler


@pytest.mark.system_test
def test_alert_to_graylog():
    logger = logging.getLogger("Dodal")
    host, port = get_graylog_configuration(False)
    set_up_graylog_handler(logger, host, port)
    alert_service = LoggingAlertService()
    alert_service.raise_alert("Test alert", "This is a test.")
