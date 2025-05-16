import pytest

from dodal.common.alerting.alert_manager import AlertManagerAlertService

ENDPOINT = "http://172.23.169.36:9093"


@pytest.mark.system_test
def test_alertmanager_alerts():
    alert_service = AlertManagerAlertService("admin", "admin", ENDPOINT)
    alert_service.get_alerts()
    alert_service.raise_alert("Test alert summary", "Test alert message")
