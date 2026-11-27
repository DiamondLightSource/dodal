import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.beamlines.i10_1 import I10JScalerCard
from dodal.devices.scaler_card import CountMode


@pytest.fixture
async def mock_i10j_scalercard(prefix: str = "BLXX-EA-DET-007:") -> I10JScalerCard:
    async with init_devices(mock=True):
        mock_i10j_scalercard = I10JScalerCard(prefix=prefix)
    return mock_i10j_scalercard


async def test_i10j_scalercard_read(mock_i10j_scalercard: I10JScalerCard):
    await assert_reading(
        mock_i10j_scalercard,
        {
            "mock_i10j_scalercard-mon-count": partial_reading(0.0),
            "mock_i10j_scalercard-tey-count": partial_reading(0.0),
            "mock_i10j_scalercard-fy-count": partial_reading(0.0),
            "mock_i10j_scalercard-fy2-count": partial_reading(0.0),
        },
    )


async def test_i10j_scalercard_configuration_has_single_card_settings(
    mock_i10j_scalercard: I10JScalerCard,
):
    await assert_configuration(
        mock_i10j_scalercard,
        {
            "mock_i10j_scalercard-controller-integration_time": partial_reading(0.0),
            "mock_i10j_scalercard-controller-count_mode": partial_reading(
                CountMode.AUTO
            ),
            "mock_i10j_scalercard-controller-delay_time": partial_reading(0.0),
        },
    )


def test_i10j_scalercard_channels_share_one_controller(
    mock_i10j_scalercard: I10JScalerCard,
):
    channels = [
        mock_i10j_scalercard.mon,
        mock_i10j_scalercard.tey,
        mock_i10j_scalercard.fy,
        mock_i10j_scalercard.fy2,
    ]
    assert all(c.controller is mock_i10j_scalercard.controller for c in channels)
