from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    ConfigSignal,
    HintedSignal,
    StandardReadable,
    wait_for_value,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class UndulatorGatestatus(str, Enum):
    open = "Open"
    close = "Closed"


class UndulatorGap(StandardReadable, Movable):
    """A collection of epics signals to control Apple 2 undulator gap motion.
    Only PV used by beamline are added the full list is here:
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDGapVelocityControl.template
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDPhaseSoftMotor.template
    """

    def __init__(self, prefix: str, name: str = ""):
        # Gap demand set point and readback
        self.user_setpoint = epics_signal_rw(
            str, prefix + "GAPSET.B", prefix + "BLGSET"
        )
        # Nothing move until this is set to 1 and it will return to 0 when done
        self.set_move = epics_signal_rw(int, prefix + "BLGSETP")
        # Gate keeper open when move is requested, closed when move is completed
        # self.gate = epics_signal_r(UndulatorGatestatus, prefix + "BLGATE")
        # These are gap velocity limit.
        self.max_velocity = epics_signal_r(float, prefix + "BLGSETVEL.HOPR")
        self.min_velocity = epics_signal_r(float, prefix + "BLGSETVEL.LOPR")
        # These are gap limit.
        self.high_limit = epics_signal_r(float, prefix + "BLGAPMTR.HLM")
        self.low_limit = epics_signal_r(float, prefix + "BLGAPMTR.LLM")

        # This is calculated acceleration from speed
        self.acceleration_time = epics_signal_r(float, prefix + "IDGSETACC")
        with self.add_children_as_readables(ConfigSignal):
            # Unit
            self.motor_egu = epics_signal_r(str, prefix + "BLGAPMTR.EGU")
            # Gap velocity
            self.velocity = epics_signal_rw(float, prefix + "BLGSETVEL")
            # Gate keeper
            self.gate = epics_signal_r(UndulatorGatestatus, prefix + "BLGATE")
        with self.add_children_as_readables(HintedSignal):
            # Gap readback value
            self.user_readback = epics_signal_r(float, prefix + "CURRGAPD")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        if await self.gate.get_value() == UndulatorGatestatus.open:
            raise RuntimeError(f"{self.name} is already in motion.")
        await self.user_setpoint.set(value=str(value))
        timeout = await self._cal_timeout()
        await self.set_move.set(value=1)
        await wait_for_value(self.gate, UndulatorGatestatus.close, timeout=timeout)

    async def _cal_timeout(self) -> float:
        vel = await self.velocity.get_value()
        cur_pos = await self.user_readback.get_value()
        target_pos = float(await self.user_setpoint.get_value())
        return abs((target_pos - cur_pos) * 2.0 / vel)
