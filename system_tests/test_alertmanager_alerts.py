import pytest

from dodal.common.alerting.alert_manager import AlertManagerAlertService

ENDPOINT = "https://yqf46943-alertmanager.diamond.ac.uk"


@pytest.mark.system_test
def test_alertmanager_alerts():
    alert_service = AlertManagerAlertService("admin", "admin", ENDPOINT)
    alert_service.get_alerts()
    alert_service.raise_alert("Test alert summary", "Test alert message")
