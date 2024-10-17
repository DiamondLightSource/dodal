from unittest.mock import ANY

import pytest
from ophyd_async.core import (
    DeviceCollector,
    assert_reading,
)

from dodal.devices.qbpm import QBPM


@pytest.fixture
async def qbpm() -> QBPM:
    async with DeviceCollector(mock=True):
        qbpm = QBPM("", name="qbpm")
    return qbpm


async def test_reading_includes_read_fields(qbpm: QBPM):
    await assert_reading(
        qbpm,
        {
            "qbpm-intensity_uA": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
        },
    )
