import pytest

from dodal.common.alerting.alert_manager import AlertManagerAlertService

ENDPOINT = "https://yqf46943-alertmanager.diamond.ac.uk"
TEST_SAMPLE_ID = 123456
TEST_VISIT = "cm12345-1"
TEST_CONTAINER = 8


@pytest.mark.requires(external="alertmanager")
def test_alertmanager_alerts():
    alert_service = AlertManagerAlertService(ENDPOINT)
    alert_service.get_alerts()
    alert_service.raise_alert(
        "Test alert summary",
        "Test alert message",
        {
            "alert_type": "Test",
            "sample_id": str(TEST_SAMPLE_ID),
            "visit": TEST_VISIT,
            "container": str(TEST_CONTAINER),
            "beamline": "i03",
        },
    )
