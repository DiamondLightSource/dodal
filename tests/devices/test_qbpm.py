import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.qbpm import QBPM


@pytest.fixture
async def qbpm() -> QBPM:
    async with init_devices(mock=True):
        qbpm = QBPM("", name="qbpm")
    return qbpm


async def test_reading_includes_read_fields(qbpm: QBPM):
    await assert_reading(
        qbpm,
        {
            "qbpm-intensity_uA": partial_reading(0.0),
        },
    )
