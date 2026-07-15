from typing import TypedDict

from ophyd_async.core import AsyncStatus
from ophyd_async.epics.core import epics_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.devices.defered_move_utils import (
    DeferMoves,
    combined_move_to_motor_setpoints,
    do_deferred_move,
)
from dodal.devices.motors import XYZStage
from dodal.log import LOGGER


class CombinedMove(TypedDict, total=False):
    """A move on multiple axes at once using a deferred move.

    Attributes:
        x (float): target x-coordinate in mm
        y (float): target y-coordinate in mm
        z (float): target z-coordinate in mm
        rx (float): target rx angle in degrees
        ry (float): target rx angle in degrees
        rz (float): target rx angle in degrees
    """

    x: float | None
    y: float | None
    z: float | None
    rx: float | None
    ry: float | None
    rz: float | None


class Hexapod(XYZStage):
    """The Hexapod that holds the sample.

    If you would like to use multiple axes at once use the combined move like:

    >>> mv(hexapod, {"x": 10.0, "y":1.0})
    """

    DEFERRED_MOVE_SET_TIMEOUT = 5

    def __init__(self, prefix: str, defer_move_pv: str, name: str = ""):
        self.rx = Motor(f"{prefix}RX")
        self.ry = Motor(f"{prefix}RY")
        self.rz = Motor(f"{prefix}RZ")
        self.defer_move = epics_signal_rw(DeferMoves, defer_move_pv)
        super().__init__(prefix, name)

    @AsyncStatus.wrap
    async def set(self, value: CombinedMove):
        """This will move all motion together in a deferred move.

        Once defer_move is on, sets to any axis do not immediately move the axis. Instead
        the setpoint will go to that value. Then, when defer_move is switched off all
        axes will move at the same time. The put callbacks on the axes themselves will
        only come back after the motion on that axis finished.
        """
        LOGGER.info("Doing hexapod deferred move")

        motor_moves = combined_move_to_motor_setpoints(value, self)

        await do_deferred_move(
            self.defer_move,
            motor_moves,
            self.DEFERRED_MOVE_SET_TIMEOUT,
        )
