import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i10_1 import I10JScalerCard


@pytest.fixture
async def mock_i10j_scalercard(prefix: str = "BLXX-EA-DET-007:") -> I10JScalerCard:
    async with init_devices(mock=True):
        mock_i10j_scalercard = I10JScalerCard(prefix=prefix)
    return mock_i10j_scalercard


async def test_i10j_scalercard_read(mock_i10j_scalercard: I10JScalerCard):
    await assert_reading(
        mock_i10j_scalercard,
        {
            "mock_i10j_scalercard-mon-readout": partial_reading(0.0),
            "mock_i10j_scalercard-tey-readout": partial_reading(0.0),
            "mock_i10j_scalercard-fy-readout": partial_reading(0.0),
            "mock_i10j_scalercard-fy2-readout": partial_reading(0.0),
        },
    )
