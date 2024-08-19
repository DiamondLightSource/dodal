import asyncio
from dataclasses import dataclass
from enum import Enum

import numpy as np
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


@dataclass
class Apple2PhasesVal:
    top_outer: str
    top_inner: str
    btm_outer: str
    btm_inner: str


@dataclass
class Apple2PhasesPv:
    top_outer: str
    top_inner: str
    btm_outer: str
    btm_inner: str


@dataclass
class Apple2Val:
    gap: str
    top_outer: str
    top_inner: str
    btm_outer: str
    btm_inner: str


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
        self.gate = epics_signal_r(UndulatorGatestatus, prefix + "BLGATE")
        # These are gap velocity limit.
        self.max_velocity = epics_signal_r(float, prefix + "BLGSETVEL.HOPR")
        self.min_velocity = epics_signal_r(float, prefix + "BLGSETVEL.LOPR")
        # These are gap limit.
        self.high_limit_travel = epics_signal_r(float, prefix + "BLGAPMTR.HLM")
        self.low_limit_travel = epics_signal_r(float, prefix + "BLGAPMTR.LLM")
        split_pv = prefix.split("-")
        self.fault = epics_signal_r(
            float,
            split_pv[0] + "-" + split_pv[1] + "-STAT" + "-" + split_pv[3] + "ANYFAULT",
        )
        # This is calculated acceleration from speed
        self.acceleration_time = epics_signal_r(float, prefix + "IDGSETACC")
        with self.add_children_as_readables(ConfigSignal):
            # Unit
            self.motor_egu = epics_signal_r(str, prefix + "BLGAPMTR.EGU")
            # Gap velocity
            self.velocity = epics_signal_rw(float, prefix + "BLGSETVEL")
        with self.add_children_as_readables(HintedSignal):
            # Gap readback value
            self.user_readback = epics_signal_r(float, prefix + "CURRGAPD")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        if await self.fault.get_value() != 0:
            raise RuntimeError(f"{self.name} is in fault state")
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

    async def get_timeout(self) -> float:
        return await self._cal_timeout()


class UndulatorPhaseMotor(StandardReadable):
    """A collection of epics signals for ID phase motion.
    Only PV used by beamline are added the full list is here:
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDPhaseSoftMotor.template


    """

    def __init__(self, prefix: str, infix: str, name: str = ""):
        """
        Parameters
        ----------

        prefix : str
            The setting prefix PV.
        infix: str
            Collection of pv that are different between beamlines
        name : str
            Name of the Id phase device
        """
        fullPV = prefix + "BL" + infix + "MTR"
        self.user_setpoint = epics_signal_w(str, fullPV[:-3] + "SET")
        self.user_setpoint_demand_readback = epics_signal_r(float, fullPV[:-3] + "DMD")
        with self.add_children_as_readables(HintedSignal):
            self.user_setpoint_readback = epics_signal_r(float, fullPV + ".RBV")

        with self.add_children_as_readables(ConfigSignal):
            self.motor_egu = epics_signal_r(str, fullPV + ".EGU")
            self.velocity = epics_signal_rw(float, fullPV + ".VELO")

        self.max_velocity = epics_signal_r(float, fullPV + ".VMAX")
        self.acceleration_time = epics_signal_rw(float, fullPV + ".ACCL")
        self.precision = epics_signal_r(int, fullPV + ".PREC")
        self.deadband = epics_signal_r(float, fullPV + ".RDBD")
        self.motor_done_move = epics_signal_r(int, fullPV + ".DMOV")
        self.low_limit_travel = epics_signal_rw(float, fullPV + ".LLM")
        self.high_limit_travel = epics_signal_rw(float, fullPV + ".HLM")
        super().__init__(name=name)


class UndlatorPhaseAxes(StandardReadable, Movable):
    """A collection of 4 phase Motor to make up"""

    def __init__(
        self,
        prefix: str,
        top_outer: str,
        top_inner: str,
        btm_outer: str,
        btm_inner: str,
        name: str = "",
    ):
        # Gap demand set point and readback
        with self.add_children_as_readables():
            self.top_outer = UndulatorPhaseMotor(prefix=prefix, infix=top_outer)
            self.top_inner = UndulatorPhaseMotor(prefix=prefix, infix=top_inner)
            self.btm_outer = UndulatorPhaseMotor(prefix=prefix, infix=btm_outer)
            self.btm_inner = UndulatorPhaseMotor(prefix=prefix, infix=btm_inner)
        # Nothing move until this is set to 1 and it will return to 0 when done
        self.set_move = epics_signal_rw(int, prefix + "BLGSETP")
        self.gate = epics_signal_r(UndulatorGatestatus, prefix + "BLGATE")
        split_pv = prefix.split("-")
        self.fault = epics_signal_r(
            float,
            split_pv[0] + "-" + split_pv[1] + "-STAT" + "-" + split_pv[3] + "ANYFAULT",
        )
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: Apple2PhasesVal) -> None:
        if await self.fault.get_value() != 0:
            raise RuntimeError(f"{self.name} is in fault state")
        if await self.gate.get_value() == UndulatorGatestatus.open:
            raise RuntimeError(f"{self.name} is already in motion.")
        await asyncio.gather(
            self.top_outer.user_setpoint.set(value=value.top_outer),
            self.top_inner.user_setpoint.set(value=value.top_inner),
            self.btm_outer.user_setpoint.set(value=value.btm_outer),
            self.btm_inner.user_setpoint.set(value=value.btm_inner),
        )
        timeout = await self._cal_timeout()
        await self.set_move.set(value=1)
        await wait_for_value(self.gate, UndulatorGatestatus.close, timeout=timeout)

    async def _cal_timeout(self) -> float:
        velos = await asyncio.gather(
            self.top_outer.velocity.get_value(),
            self.top_inner.velocity.get_value(),
            self.btm_outer.velocity.get_value(),
            self.btm_inner.velocity.get_value(),
        )
        cur_pos = await asyncio.gather(
            self.top_outer.user_setpoint_demand_readback.get_value(),
            self.top_inner.user_setpoint_demand_readback.get_value(),
            self.btm_outer.user_setpoint_demand_readback.get_value(),
            self.btm_inner.user_setpoint_demand_readback.get_value(),
        )
        target_pos = await asyncio.gather(
            self.top_outer.user_setpoint_readback.get_value(),
            self.top_inner.user_setpoint_readback.get_value(),
            self.btm_outer.user_setpoint_readback.get_value(),
            self.btm_inner.user_setpoint_readback.get_value(),
        )
        move_time = np.abs(np.divide(tuple(np.subtract(target_pos, cur_pos)), velos))

        return move_time.max() * 2

    async def get_timeout(self) -> float:
        return await self._cal_timeout()
