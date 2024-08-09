import asyncio
from dataclasses import dataclass
from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    ConfigSignal,
    HintedSignal,
    StandardReadable,
    wait_for_value,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw, epics_signal_w


class UndulatorGatestatus(str, Enum):
    open = "Open"
    close = "Closed"


class UndulatorGap(StandardReadable, Movable):
    """A device with a collection of epics signals to set Apple 2 undulator gap motion.
    Only PV used by beamline are added the full list is here:
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDGapVelocityControl.template
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDPhaseSoftMotor.template
    """

    def __init__(self, prefix: str, name: str = ""):
        """
        Constructs all the necessary PV for the pundulatorGap.

        Parameters
        ----------
            prefix : str
                Beamline specific part of the PV
            name : str
                Name of the Id device

        """

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


@dataclass
class PhaseAxisPv:
    """
    This is use to adjust different pv on different beamlines.

    Format:
        $(prefix)$(set_pv/read_pv):BL$(axis_pv)MTR

    example:
        SR10I-MO-SERVC-01:BLRPQ1SET -> for setting
        SR10I-MO-SERVO-03:MOT.RBV   -> for getting

        set_pv = "SERVC-01"
        read_pv: "SERVO-03"
        axis_pv = "RPQ1"
    """

    set_pv: str
    read_pv: str
    axis_pv: str


class UndulatorPhaseMotor(StandardReadable):
    """A collection of epics signals for ID phase motion.
    Only PV used by beamline are added the full list is here:
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDPhaseSoftMotor.template


    """

    def __init__(self, prefix: str, infix: PhaseAxisPv, name: str = ""):
        """
        Parameters
        ----------

        prefix : str
            The setting prefix PV.
        infix: PhaseAxisPv, : str
            Collection of pv that are different between beamlines
        name : str
            Name of the Id phase device
        """

        self.user_setpoint = epics_signal_w(
            str, prefix + infix.set_pv + ":BL" + infix.axis_pv + "SET"
        )
        self.user_setpoint_readback = epics_signal_r(
            float, prefix + infix.read_pv + ":MOT"
        )
        with self.add_children_as_readables(HintedSignal):
            self.user_readback = epics_signal_r(
                float, prefix + infix.read_pv + ":MOT.RBV"
            )
        super().__init__(name=name)


class UndlatorPhaseAxes(StandardReadable, Movable):
    """A collection of 4 phase Motor to make up"""

    def __init__(
        self,
        prefix: str,
        top_outer: PhaseAxisPv,
        top_inner: PhaseAxisPv,
        btm_outer: PhaseAxisPv,
        btm_inner: PhaseAxisPv,
        name: str = "",
    ):
        # Gap demand set point and readback
        with self.add_children_as_readables():
            self.top_outer = UndulatorPhaseMotor(prefix=prefix, infix=top_outer)
            self.top_inner = UndulatorPhaseMotor(prefix=prefix, infix=top_inner)
            self.btm_outer = UndulatorPhaseMotor(prefix=prefix, infix=btm_outer)
            self.btm_inner = UndulatorPhaseMotor(prefix=prefix, infix=btm_inner)
        # Nothing move until this is set to 1 and it will return to 0 when done
        self.set_move = epics_signal_rw(int, prefix + top_inner.set_pv + ":BLGSETP")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: list) -> None:
        await asyncio.gather(
            self.top_outer.user_setpoint.set(value[0]),
            self.top_inner.user_setpoint.set(value[1]),
            self.btm_outer.user_setpoint.set(value[2]),
            self.btm_inner.user_setpoint.set(value[3]),
        )
        await self.set_move.set(value=1)
