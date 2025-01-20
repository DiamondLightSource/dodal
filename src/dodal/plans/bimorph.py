from enum import Enum

import bluesky.plan_stubs as bps
from bluesky.preprocessors import run_decorator, stage_decorator
from numpy import linspace
from ophyd_async.core import StandardDetector

from dodal.devices.bimorph_mirror import BimorphMirror
from dodal.devices.slits import Slits


class SlitDimension(Enum):
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
        yield from bps.mv(slits.x_gap, gap)  # type: ignore
        yield from bps.mv(slits.x_centre, center)  # type: ignore
    else:
        yield from bps.mv(slits.y_gap, gap)  # type: ignore
        yield from bps.mv(slits.y_centre, center)  # type: ignore


def bimorph_optimisation(
    mirror: BimorphMirror,
    slits: Slits,
    oav: StandardDetector,
    voltage_increment: float,
    active_dimension: SlitDimension,
    active_slit_center_start: float,
    active_slit_center_end: float,
    active_slit_size: float,
    inactive_slit_center: float,
    inactive_slit_size: float,
    number_of_slit_positions: int,
    bimorph_settle_time: float,
    initial_voltage_list: list | None = None,
):
    """Plan for performing bimorph mirror optimisation.

    Bluesky plan that performs a series of pencil beam scans across one axis of a
    bimorph mirror, of using a 2-dimensional slit.

    Args:
        bimorph: BimorphMirror to move
        slit: Slits
        oav: oav on-axis viewer
        voltage_increment: float voltage increment applied to each bimorph electrode
        active_dimension: SlitDimension that slit will move in (X or Y)
        active_slit_center_start: float start position of center of slit in active dimension
        active_slit_center_end: float final position of center of slit in active dimension
        active_slit_size: float size of slit in active dimension
        inactive_slit_center: float center of slit in inactive dimension
        inactive_slit_size: float size of slit in inactive dimension
        number_of_slit_positions: int number of slit positions per pencil beam scan
        bimorph_settle_time: float time in seconds to wait after bimorph move
        initial_voltage_list: optional list[float] starting voltages for bimorph (defaults to current voltages)
    """
    # Get voltages to return to after plan:
    original_voltage_list = []

    for channel in mirror.channels.values():
        position = yield from bps.rd(channel.output_voltage)
        original_voltage_list.append(position)

    # Get slit position to return to after plan:
    original_x_gap = yield from bps.rd(slits.x_gap)
    original_y_gap = yield from bps.rd(slits.y_gap)
    original_x_center = yield from bps.rd(slits.x_centre)
    original_y_center = yield from bps.rd(slits.y_centre)

    # If a starting set of voltages is not provided, default to current:
    if initial_voltage_list is None:
        initial_voltage_list = original_voltage_list

    if active_dimension == SlitDimension.X:
        inactive_dimension = SlitDimension.Y
    else:
        inactive_dimension = SlitDimension.X

    # Move slits into starting position:
    yield from move_slits(
        slits, active_dimension, active_slit_size, active_slit_center_start
    )
    yield from move_slits(
        slits, inactive_dimension, inactive_slit_size, inactive_slit_center
    )

    @stage_decorator(oav, slits, mirror)
    @run_decorator
    def outer():
        """Outer part of two-movable scan, which moves bimorph and calls inner."""
        yield from inner_scan(
            mirror,
            slits,
            oav,
            active_dimension,
            active_slit_center_start,
            active_slit_center_end,
            active_slit_size,
            number_of_slit_positions,
        )
        for i, channel in enumerate(mirror.channels.values()):
            yield from bps.mv(channel, initial_voltage_list[i] + voltage_increment)  # type: ignore
            yield from bps.sleep(bimorph_settle_time)

            yield from inner_scan(
                mirror,
                slits,
                oav,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                number_of_slit_positions,
            )

    yield from outer()

    # return to start slit positions
    yield from move_slits(slits, SlitDimension.X, original_x_gap, original_x_center)
    yield from move_slits(slits, SlitDimension.Y, original_y_gap, original_y_center)
    # return to start voltages
    for value, channel in zip(
        original_voltage_list, mirror.channels.values(), strict=True
    ):
        yield from bps.mv(channel, value)  # type: ignore


def inner_scan(
    mirror: BimorphMirror,
    slits: Slits,
    oav: StandardDetector,
    active_dimension: SlitDimension,
    active_slit_center_start: float,
    active_slit_center_end: float,
    active_slit_size: float,
    number_of_slit_positions: int,
):
    """Inner part of two-movable scan, which moves Slits and performs a read.

    Args:
        mirror: BimorphMirror to move
        slit: Slits
        oav: oav on-axis viewer
        active_dimension: SlitDimension that slit will move in (X or Y)
        active_slit_center_start: float start position of center of slit in active dimension
        active_slit_center_end: float final position of center of slit in active dimension
        active_slit_size: float size of slit in active dimension
        number_of_slit_positions: int number of slit positions per pencil beam scan
    """
    for value in linspace(
        active_slit_center_start, active_slit_center_end, number_of_slit_positions
    ):
        yield from move_slits(slits, active_dimension, active_slit_size, value)
        yield from bps.trigger_and_read(oav, slits, mirror)  # type: ignore
