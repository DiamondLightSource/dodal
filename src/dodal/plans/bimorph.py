from collections.abc import Generator
from dataclasses import dataclass
from enum import Enum
from typing import Any

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky.protocols import Preparable, Readable
from bluesky.utils import MsgGenerator
from numpy import linspace
from ophyd_async.core import TriggerInfo

from dodal.devices.bimorph_mirror import BimorphMirror
from dodal.devices.slits import Slits


class SlitDimension(str, Enum):
    """Enum representing the dimensions of a 2d slit

    Used to describe which dimension the pencil beam scan should move across.
    The other dimension will be held constant.

    Attributes:
        X: Represents X dimension
        Y: Represents Y dimension
    """

    X = "X"
    Y = "Y"


def move_slits(slits: Slits, dimension: SlitDimension, gap: float, center: float):
    """Moves ones dimension of Slits object to given position.

    Args:
        slits: Slits to move
        dimension: SlitDimension (X or Y)
        gap: float size of gap
        center: float position of center
    """
    if dimension == SlitDimension.X:
        yield from bps.mv(slits.x_gap, gap)
        yield from bps.mv(slits.x_centre, center)
    else:
        yield from bps.mv(slits.y_gap, gap)
        yield from bps.mv(slits.y_centre, center)


def check_valid_bimorph_state(
    voltage_list: list[float], abs_range: float, abs_diff: float
) -> bool:
    """Checks that a set of bimorph voltages is valid.
    Args:
        voltage_list: float amount each actuator will be increased by per scan
        abs_range: float absolute value of maximum possible voltage of each actuator
        abs_diff: float absolute maximum difference between two consecutive actuators

    Returns:
        Bool representing state validity
    """
    for voltage in voltage_list:
        if abs(voltage) > abs_range:
            return False

    for i in range(len(voltage_list) - 1):
        if abs(voltage_list[i] - voltage_list[i - 1]) > abs_diff:
            return False

    return True


def validate_bimorph_plan(
    initial_voltage_list: list[float],
    voltage_increment: float,
    abs_range: float,
    abs_diff: float,
) -> bool:
    """Checks that every position the bimorph will move through will not error.

    Args:
        initial_voltage_list: float list starting position
        voltage_increment: float amount each actuator will be increased by per scan
        abs_range: float absolute value of maximum possible voltage of each actuator
        abs_diff: float absolute maximum difference between two consecutive actuators

    Raises:
        Exception if the plan will lead to an error state"""
    voltage_list = initial_voltage_list.copy()

    if not check_valid_bimorph_state(voltage_list, abs_range, abs_diff):
        raise ValueError(f"Bimorph plan reaches invalid state at: {voltage_list}")

    for i in range(len(initial_voltage_list)):
        voltage_list[i] += voltage_increment

        if not check_valid_bimorph_state(voltage_list, abs_range, abs_diff):
            raise ValueError(f"Bimorph plan reaches invalid state at: {voltage_list}")

    return True


@dataclass
class BimorphState:
    """Data class containing positions of BimorphMirror and Slits"""

    voltages: list[float]
    x_gap: float
    y_gap: float
    x_center: float
    y_center: float


def capture_bimorph_state(mirror: BimorphMirror, slits: Slits):
    """Plan stub that captures current position of BimorphMirror and Slits.

    Args:
        mirror: BimorphMirror to read from
        slits: Slits to read from

    Returns:
        A BimorphState containing BimorphMirror and Slits positions"""
    original_voltage_list = []

    for channel in mirror.channels.values():
        position = yield from bps.rd(channel.output_voltage)
        original_voltage_list.append(position)

    original_x_gap = yield from bps.rd(slits.x_gap)
    original_y_gap = yield from bps.rd(slits.y_gap)
    original_x_center = yield from bps.rd(slits.x_centre)
    original_y_center = yield from bps.rd(slits.y_centre)
    return BimorphState(
        original_voltage_list,
        original_x_gap,
        original_y_gap,
        original_x_center,
        original_y_center,
    )


def restore_bimorph_state(mirror: BimorphMirror, slits: Slits, state: BimorphState):
    """Moves BimorphMirror and Slits to state given in BirmophState.

    Args:
        mirror: BimorphMirror to move
        slits: Slits to move
        state: BimorphState to move to.
    """
    yield from move_slits(slits, SlitDimension.X, state.x_gap, state.x_center)
    yield from move_slits(slits, SlitDimension.Y, state.y_gap, state.y_center)

    yield from bps.mv(mirror, state.voltages)  # type: ignore


def bimorph_position_generator(
    initial_voltage_list: list[float], voltage_increment: float
) -> Generator[list[float], None, None]:
    """Generator that produces bimorph positions, starting with the initial_voltage_list.

    Args:
        initial_voltage_list: list starting position for bimorph
        voltage_increment: float amount to increase each actuator by in turn

    Yields:
        List bimorph positions, starting with initial_voltage_list
    """
    voltage_list = initial_voltage_list.copy()

    for i in range(-1, len(initial_voltage_list)):
        yield [
            voltage + voltage_increment if i >= j else voltage
            for (j, voltage) in enumerate(voltage_list)
        ]


def bimorph_optimisation(
    detectors: list[Readable],
    mirror: BimorphMirror,
    slits: Slits,
    voltage_increment: float,
    active_dimension: SlitDimension,
    active_slit_center_start: float,
    active_slit_center_end: float,
    active_slit_size: float,
    inactive_slit_center: float,
    inactive_slit_size: float,
    number_of_slit_positions: int,
    bimorph_settle_time: float,
    slit_settle_time: float,
    initial_voltage_list: list | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Plan for performing bimorph mirror optimisation.

    Bluesky plan that performs a series of pencil beam scans across one axis of a
    bimorph mirror, of using a 2-dimensional slit.

    Args:
        detectors: list[Readable] detectors
        bimorph: BimorphMirror to move
        slit: Slits
        voltage_increment: float voltage increment applied to each bimorph electrode
        active_dimension: SlitDimension that slit will move in (X or Y)
        active_slit_center_start: float start position of center of slit in active dimension
        active_slit_center_end: float final position of center of slit in active dimension
        active_slit_size: float size of slit in active dimension
        inactive_slit_center: float center of slit in inactive dimension
        inactive_slit_size: float size of slit in inactive dimension
        number_of_slit_positions: int number of slit positions per pencil beam scan
        bimorph_settle_time: float time in seconds to wait after bimorph move
        slit_settle_time: float time in seconds to wait after slit move
        initial_voltage_list: optional list[float] starting voltages for bimorph (defaults to current voltages)
        metadata: optional dict[str, Any] metadata to add to start document
    """

    _metadata = {
        "plan_args": {
            "detectors": {det.name for det in detectors},
            "mirror": mirror.name,
            "slits": slits.name,
            "voltage_increment": voltage_increment,
            "active_dimension": active_dimension,
            "active_slit_center_start": active_slit_center_start,
            "active_slit_center_end": active_slit_center_end,
            "active_slit_size": active_slit_size,
            "inactive_slit_center": inactive_slit_center,
            "inactive_slit_size": inactive_slit_size,
            "number_of_slit_positions": number_of_slit_positions,
            "bimorph_settle_time": bimorph_settle_time,
            "slit_settle_time": slit_settle_time,
            "initial_voltage_list": initial_voltage_list,
        },
        "plan_name": "bimorph_optimisation",
        "shape": [len(mirror.channels), number_of_slit_positions],
        **(metadata or {}),
    }

    state = yield from capture_bimorph_state(mirror, slits)

    # If a starting set of voltages is not provided, default to current:
    initial_voltage_list = initial_voltage_list or state.voltages

    bimorph_positions = bimorph_position_generator(
        initial_voltage_list, voltage_increment
    )

    validate_bimorph_plan(initial_voltage_list, voltage_increment, 1000, 500)

    inactive_dimension = (
        SlitDimension.Y if active_dimension == SlitDimension.X else SlitDimension.X
    )

    @bpp.run_decorator(md=_metadata)
    @bpp.stage_decorator((*detectors, mirror, slits))
    def outer_scan():
        """Outer plan stub, which moves mirror and calls inner_scan."""
        for detector in detectors:
            if isinstance(detector, Preparable):
                yield from bps.prepare(detector, TriggerInfo(), wait=True)

        stream_name = "0"
        yield from bps.declare_stream(*detectors, mirror, slits, name=stream_name)

        # Move slits into starting position:
        yield from move_slits(
            slits, active_dimension, active_slit_size, active_slit_center_start
        )
        yield from move_slits(
            slits, inactive_dimension, inactive_slit_size, inactive_slit_center
        )
        yield from bps.sleep(slit_settle_time)

        for bimorph_position in bimorph_positions:
            yield from bps.mv(
                mirror,  # type: ignore
                bimorph_position,  # type: ignore
            )
            yield from bps.sleep(bimorph_settle_time)

            yield from bps.declare_stream(*detectors, mirror, slits, name=stream_name)

            yield from inner_scan(
                detectors,
                mirror,
                slits,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                number_of_slit_positions,
                slit_settle_time,
                stream_name,
            )

            stream_name = str(int(stream_name) + 1)

    yield from outer_scan()

    yield from restore_bimorph_state(mirror, slits, state)


def inner_scan(
    detectors: list[Readable],
    mirror: BimorphMirror,
    slits: Slits,
    active_dimension: SlitDimension,
    active_slit_center_start: float,
    active_slit_center_end: float,
    active_slit_size: float,
    number_of_slit_positions: int,
    slit_settle_time: float,
    stream_name: str,
):
    """Inner plan stub, which moves Slits and performs a read.

    Args:
        mirror: BimorphMirror to move
        slit: Slits
        oav: oav on-axis viewer
        active_dimension: SlitDimension that slit will move in (X or Y)
        active_slit_center_start: float start position of center of slit in active dimension
        active_slit_center_end: float final position of center of slit in active dimension
        active_slit_size: float size of slit in active dimension
        number_of_slit_positions: int number of slit positions per pencil beam scan
        slit_settle_time: float time in seconds to wait after slit move
        stream_name: str name to pass to trigger_and_read
    """
    for value in linspace(
        active_slit_center_start, active_slit_center_end, number_of_slit_positions
    ):
        yield from move_slits(slits, active_dimension, active_slit_size, value)
        yield from bps.sleep(slit_settle_time)
        yield from bps.trigger_and_read([*detectors, mirror, slits], name=stream_name)
