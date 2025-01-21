from collections.abc import Generator
from pathlib import Path
from unittest.mock import ANY

import pytest
from bluesky.run_engine import RunEngine
from bluesky.utils import Msg
from numpy import linspace
from ophyd_async.core import (
    DeviceCollector,
    StandardDetector,
)
from ophyd_async.sim.demo import PatternDetector
from ophyd_async.testing import callback_on_mock_put, set_mock_value

from dodal.devices.bimorph_mirror import BimorphMirror
from dodal.devices.slits import Slits
from dodal.plans.bimorph import SlitDimension, bimorph_optimisation, move_slits


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
def initial_voltage_list(mirror_with_mocked_put) -> list[float]:
    return [0.0 for _ in range(len(mirror_with_mocked_put.channels))]


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


def move_slits_message_generator(
    slits: Slits, dimension: SlitDimension, gap: float, center: float
) -> Generator[Msg, None, None]:
    """Generates messages produced by move_slits
    Args:
        slits: Slits to move
        dimension: SlitDimension (X or Y)
        gap: float size of gap
        center: float position of center

    Yields:
        A series of Msg objects which would be yielded by move_slits
    """
    if dimension == SlitDimension.X:
        yield Msg("set", slits.x_gap, gap, group=ANY)
        yield Msg("wait", None, group=ANY)
        yield Msg("set", slits.x_centre, center, group=ANY)
        yield Msg("wait", None, group=ANY)

    else:
        yield Msg("set", slits.y_gap, gap, group=ANY)
        yield Msg("wait", None, group=ANY)
        yield Msg("set", slits.y_centre, center, group=ANY)
        yield Msg("wait", None, group=ANY)


def inner_scan_message_generator(
    mirror: BimorphMirror,
    slits: Slits,
    oav: StandardDetector,
    active_dimension: SlitDimension,
    active_slit_center_start: float,
    active_slit_center_end: float,
    active_slit_size: float,
    number_of_slit_positions: int,
) -> Generator[Msg, None, None]:
    """Generates messages produced by inner_scan.

    Args:
        mirror: BimorphMirror to move
        slit: Slits
        oav: oav on-axis viewer
        active_dimension: SlitDimension that slit will move in (X or Y)
        active_slit_center_start: float start position of center of slit in active dimension
        active_slit_center_end: float final position of center of slit in active dimension
        active_slit_size: float size of slit in active dimension
        number_of_slit_positions: int number of slit positions per pencil beam scan

    Yields:
        A series of Msg objects which would be yielded by inner_scan"""
    for value in linspace(
        active_slit_center_start, active_slit_center_end, number_of_slit_positions
    ):
        yield from move_slits_message_generator(
            slits, active_dimension, active_slit_size, value
        )
        yield Msg("trigger", oav, group=ANY)
        yield Msg("wait", None, group=ANY)
        yield Msg("wait", None, group=ANY)
        for device in [oav, slits, mirror]:
            yield Msg("read", device)
        yield Msg("save", None)


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
    plan = bimorph_optimisation(
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

    for msg in inner_scan_message_generator(
        mirror_with_mocked_put,
        slits,
        oav,
        active_dimension,
        active_slit_center_start,
        active_slit_center_end,
        active_slit_size,
        number_of_slit_positions,
    ):
        assert msg in plan
