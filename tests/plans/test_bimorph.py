from unittest.mock import ANY

import pytest
from bluesky.run_engine import RunEngine
from bluesky.utils import Msg
from ophyd_async.core import DeviceCollector, StandardDetector
from ophyd_async.epics.adsimdetector import SimDetector
from ophyd_async.testing import callback_on_mock_put, set_mock_value

from dodal.devices.slits import Slits
from dodal.plans.bimorph import SlitDimension, move_slits


@pytest.fixture
def slits(RE: RunEngine) -> Slits:
    """Mock slits with propagation from setpoint to readback."""
    with DeviceCollector(mock=True):
        slits = Slits("FAKE-PREFIX:")

    for motor in [slits.x_gap, slits.y_gap, slits.x_centre, slits.y_centre]:

        def callback(value, wait=False, signal=motor.user_readback):
            breakpoint()
            set_mock_value(signal, value)

        callback_on_mock_put(motor.user_setpoint, callback)
    return slits


@pytest.fixture
def oav(static_path_provider) -> StandardDetector:
    return SimDetector("FAKE-PREFIX", path_provider=static_path_provider)


@pytest.mark.parametrize("dimension", [SlitDimension.X, SlitDimension.Y])
@pytest.mark.parametrize("gap", [1.0])
@pytest.mark.parametrize("center", [2.0])
async def test_move_slits(
    slits: Slits,
    dimension: SlitDimension,
    gap: float,
    center: float,
):
    messages = list(move_slits(slits, dimension, gap, center))

    if dimension == SlitDimension.X:
        gap_signal = slits.x_gap
        centre_signal = slits.x_centre
    else:
        gap_signal = slits.y_gap
        centre_signal = slits.y_centre

    assert [
        Msg("set", gap_signal, gap, group=ANY),
        Msg("wait", None, group=ANY),
        Msg("set", centre_signal, center, group=ANY),
        Msg("wait", None, group=ANY),
    ] == messages


async def test_bimorph_optimisation(
    mirror_with_mocked_put,
    slits,
    oav,
    voltage_increment,
    active_dimension,
    active_slit_center_start,
    active_slit_center_end,
    active_slit_size,
    inactive_slit_center,
    inactive_slit_size,
    number_of_slit_positions,
    bimorph_settle_time,
    initial_voltage_list,
): ...
