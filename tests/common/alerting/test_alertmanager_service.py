from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from dodal.common.alerting.alert_manager import AlertManagerAlertService

ALERTMANAGER_URL = "https://alertmanager.bogus.com"
GRAYLOG_STREAM = "123456789"

TEST_SAMPLE_ID = 123456
TEST_VISIT = "cm12345-1"
TEST_CONTAINER = 8


@pytest.fixture()
def metadata():
    return {
        "sample_id": TEST_SAMPLE_ID,
        "visit": TEST_VISIT,
        "container": TEST_CONTAINER,
    }


@pytest.fixture(autouse=True)
def patch_now():
    with patch(
        "dodal.common.alerting.alert_manager.datetime", spec=datetime
    ) as mock_datetime:
        mock_datetime.now.return_value = datetime.fromisoformat(
            "2025-05-22T12:04:23.123Z"
        )
        yield mock_datetime


@patch("dodal.common.alerting.alert_manager.requests.Session")
def test_alertmanager_alert(
    session_cls: MagicMock,
    metadata: dict[str, str],
):
    alert_service = AlertManagerAlertService(ALERTMANAGER_URL, GRAYLOG_STREAM)
    alert_service.raise_alert("Test summary", "Test content", metadata)
    with session_cls() as session:
        post_call = session.method_calls[0]
        assert post_call.args[0] == f"{ALERTMANAGER_URL}/api/v2/alerts"
        actual_metadata = post_call.kwargs["json"]
        assert actual_metadata[0]["generatorURL"] == (
            "http://graylog.diamond.ac.uk/streams/123456789/search?q=&rangetype=absolute&from=2025-05-22T11%3A49%3A23"
            ".123"
            "%2B00%3A00Z&to=2025-05-22T12%3A04%3A23.123%2B00%3A00Z"
        )
