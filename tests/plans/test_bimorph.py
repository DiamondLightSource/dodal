import asyncio
from pathlib import Path
from unittest.mock import ANY, call

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from bluesky.utils import Msg
from ophyd_async.core import DeviceCollector, StandardDetector, walk_rw_signals
from ophyd_async.sim.demo import PatternDetector
from ophyd_async.testing import callback_on_mock_put, get_mock_put, set_mock_value

from dodal.devices.bimorph_mirror import BimorphMirror, BimorphMirrorStatus
from dodal.devices.slits import Slits
from dodal.plans.bimorph import (
    SlitDimension,
    bimorph_optimisation,
    capture_bimorph_state,
    move_slits,
    restore_bimorph_state,
)

# VALID_BIMORPH_CHANNELS = [8, 12, 16, 24]
VALID_BIMORPH_CHANNELS = [2]


@pytest.fixture(params=VALID_BIMORPH_CHANNELS)
def mirror(request, RE: RunEngine) -> BimorphMirror:
    number_of_channels = request.param

    with DeviceCollector(mock=True):
        bm = BimorphMirror(
            prefix="FAKE-PREFIX:",
            number_of_channels=number_of_channels,
        )

    return bm


@pytest.fixture
def mirror_with_mocked_put(mirror: BimorphMirror):
    async def busy_idle():
        await asyncio.sleep(0)
        set_mock_value(mirror.status, BimorphMirrorStatus.BUSY)
        await asyncio.sleep(0)
        set_mock_value(mirror.status, BimorphMirrorStatus.IDLE)

    async def status(*_, **__):
        asyncio.create_task(busy_idle())

    for signal in walk_rw_signals(mirror).values():
        callback_on_mock_put(signal, status)

    for channel in mirror.channels.values():

        def vout_propogation_and_status(
            value: float, wait=False, signal=channel.output_voltage
        ):
            signal.set(value, wait=wait)
            asyncio.create_task(busy_idle())

        callback_on_mock_put(channel.target_voltage, vout_propogation_and_status)

    return mirror


@pytest.fixture
def slits(RE: RunEngine) -> Slits:
    """Mock slits with propagation from setpoint to readback."""
    with DeviceCollector(mock=True):
        slits = Slits("FAKE-PREFIX:")

    for motor in [slits.x_gap, slits.y_gap, slits.x_centre, slits.y_centre]:
        # Set velocity to avoid zero velocity error:
        set_mock_value(motor.velocity, 1)

        def callback(value, wait=False, signal=motor.user_readback):
            set_mock_value(signal, value)

        callback_on_mock_put(motor.user_setpoint, callback)
    return slits


@pytest.fixture
async def oav(RE: RunEngine, tmp_path: Path) -> StandardDetector:
    with DeviceCollector(mock=True):
        det = PatternDetector(tmp_path)
    return det


@pytest.fixture
def initial_voltage_list(mirror) -> list[float]:
    return [0.0 for _ in range(len(mirror.channels))]


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


def test_save_and_restore(RE: RunEngine, mirror: BimorphMirror, slits: Slits):
    signals = [
        slits.x_gap.user_setpoint,
        slits.y_gap.user_setpoint,
        slits.x_centre.user_setpoint,
        slits.y_centre.user_setpoint,
        mirror.channels[1].output_voltage,
    ]
    puts = [get_mock_put(signal) for signal in signals]

    def plan():
        state = yield from capture_bimorph_state(mirror, slits)

        for signal in signals:
            yield from bps.abs_set(signal, 4.0, wait=True)

        yield from restore_bimorph_state(mirror, slits, state)

    RE(plan())

    for put in puts:
        assert put.call_args_list == [call(4.0, wait=True), call(0.0, wait=True)]


@pytest.mark.parametrize("voltage_increment", [100.0])
@pytest.mark.parametrize("active_dimension", [SlitDimension.X, SlitDimension.Y])
@pytest.mark.parametrize("active_slit_center_start", [0.0])
@pytest.mark.parametrize("active_slit_center_end", [200])
@pytest.mark.parametrize("active_slit_size", [0.05])
@pytest.mark.parametrize("inactive_slit_center", [0.0])
@pytest.mark.parametrize("inactive_slit_size", [0.05])
@pytest.mark.parametrize("number_of_slit_positions", [3])
@pytest.mark.parametrize("bimorph_settle_time", [0.0])
async def test_bimorph_optimisation(
    RE: RunEngine,
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
):
    bimorph_optimisation(
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
    )
