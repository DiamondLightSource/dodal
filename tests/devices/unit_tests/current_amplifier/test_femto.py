from unittest import mock
from unittest.mock import AsyncMock

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DeviceCollector,
)

from dodal.devices.current_amplifiers import (
    Femto3xxGainTable,
    Femto3xxRaiseTime,
    FemtoDDPCA,
)


@pytest.fixture
async def mock_femto(prefix: str = "BLXX-EA-DET-007:") -> FemtoDDPCA:
    async with DeviceCollector(mock=True):
        mock_femto = FemtoDDPCA(
            prefix=prefix,
            gain_table=Femto3xxGainTable,
            raise_timetable=Femto3xxRaiseTime,
            name="mock_femto",
        )
    assert mock_femto.name == "mock_femto"
    return mock_femto


@pytest.mark.parametrize(
    "gain, wait_time, gain_value",
    [
        (["sen_1", 0.8e-3, "10^4"]),
        (["sen_3", 0.8e-3, "10^6"]),
        (["sen_5", 2.3e-3, "10^8"]),
        (["sen_7", 17e-3, "10^10"]),
        (["sen_10", 350e-3, "10^13"]),
    ],
)
@pytest.mark.asyncio
@mock.patch("asyncio.sleep")
async def test_femto_set(
    sleep: AsyncMock, mock_femto: FemtoDDPCA, RE: RunEngine, gain, wait_time, gain_value
):
    await mock_femto.set(gain)
    assert await mock_femto.gain.get_value() == gain_value
    sleep.assert_called_once_with(wait_time)
