import asyncio
from dataclasses import dataclass
from typing import Generic, TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, Reference, StandardReadable, wait_for_value
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.insertion_device.apple2_motors import (
    UndulatorGap,
    UndulatorPhaseMotor,
)
from dodal.devices.insertion_device.apple2_undulator_base import (
    SafeUndulatorMoverBase,
    estimate_motor_timeout,
    estimate_motor_timeout_from_signals,
)
from dodal.devices.insertion_device.enum import UndulatorGateStatus
from dodal.log import LOGGER


@dataclass
class Apple2LockedPhasesVal:
    top_outer: float
    btm_inner: float


@dataclass
class Apple2PhasesVal(Apple2LockedPhasesVal):
    top_inner: float
    btm_outer: float


@dataclass
class Apple2Val:
    gap: float
    phase: Apple2LockedPhasesVal | Apple2PhasesVal

    def extract_phase_val(self):
        return self.phase


Apple2PhaseValType = TypeVar("Apple2PhaseValType", bound=Apple2LockedPhasesVal)


class UndulatorLockedPhaseAxes(SafeUndulatorMoverBase[Apple2PhaseValType]):
    """Two phase Motor to make up the locked id phase motion."""

    def __init__(
        self,
        prefix: str,
        top_outer: str,
        btm_inner: str,
        name: str = "",
    ):
        # Gap demand set point and readback
        with self.add_children_as_readables():
            self.top_outer = UndulatorPhaseMotor(prefix=f"{prefix}BL{top_outer}")
            self.btm_inner = UndulatorPhaseMotor(prefix=f"{prefix}BL{btm_inner}")
        # Nothing move until this is set to 1 and it will return to 0 when done.
        self.set_move = epics_signal_rw(int, f"{prefix}BL{top_outer}" + "MOVE")
        self.axes = [self.top_outer, self.btm_inner]
        super().__init__(prefix, name)

    async def set_demand_positions(self, value: Apple2PhaseValType) -> None:
        await asyncio.gather(
            self.top_outer.user_setpoint.set(value=value.top_outer),
            self.btm_inner.user_setpoint.set(value=value.btm_inner),
        )

    async def get_timeout(self) -> float:
        """Get all motor speed, current positions and target positions to calculate
        required timeout.
        """
        timeouts = await asyncio.gather(
            *[
                estimate_motor_timeout_from_signals(
                    axis.user_setpoint_readback,
                    axis.user_readback,
                    axis.velocity,
                )
                for axis in self.axes
            ]
        )
        # A 2.0 multiplier is required to prevent premature motor timeouts in phase
        # axes as it is a master-slave system, where the slave's movement,
        # being dependent on the master, can take up to twice as long to complete.
        return max(timeouts) * 2.0


class UndulatorPhaseAxes(UndulatorLockedPhaseAxes[Apple2PhasesVal]):
    """A collection of 4 phase Motor to make up the full id phase motion. We are using
    the diamond PV convention. e.g.::

        top_outer == Q1
        top_inner == Q2
        btm_inner == q3
        btm_outer == q4
    """  # noqa D415

    def __init__(
        self,
        prefix: str,
        top_outer: str,
        top_inner: str,
        btm_inner: str,
        btm_outer: str,
        name: str = "",
    ):
        # Gap demand set point and readback
        with self.add_children_as_readables():
            self.top_inner = UndulatorPhaseMotor(prefix=f"{prefix}BL{top_inner}")
            self.btm_outer = UndulatorPhaseMotor(prefix=f"{prefix}BL{btm_outer}")

        super().__init__(prefix, top_outer=top_outer, btm_inner=btm_inner, name=name)
        self.axes.extend([self.top_inner, self.btm_outer])

    async def set_demand_positions(self, value: Apple2PhasesVal) -> None:
        await asyncio.gather(
            self.top_outer.user_setpoint.set(value=value.top_outer),
            self.top_inner.user_setpoint.set(value=value.top_inner),
            self.btm_inner.user_setpoint.set(value=value.btm_inner),
            self.btm_outer.user_setpoint.set(value=value.btm_outer),
        )


class UndulatorJawPhase(SafeUndulatorMoverBase[float]):
    """A JawPhase movable, this is use for moving the jaw phase which is use to control
    the linear arbitrary polarisation but only on some of the beamline.
    """

    def __init__(
        self,
        prefix: str,
        move_pv: str,
        jaw_phase: str = "JAW",
        name: str = "",
    ):
        # Gap demand set point and readback
        with self.add_children_as_readables():
            self.jaw_phase = UndulatorPhaseMotor(prefix=f"{prefix}BL{jaw_phase}")
        self.set_move = epics_signal_rw(int, f"{prefix}BL{move_pv}" + "MOVE")
        super().__init__(prefix, name)

    async def set_demand_positions(self, value: float) -> None:
        await self.jaw_phase.user_setpoint.set(value=value)

    async def get_timeout(self) -> float:
        """Get motor speed, current position and target position to calculate required
        timeout.
        """
        setpoint, readback, velocity = await asyncio.gather(
            self.jaw_phase.user_setpoint_readback.get_value(),
            self.jaw_phase.user_readback.get_value(),
            self.jaw_phase.velocity.get_value(),
        )
        return estimate_motor_timeout(setpoint, readback, velocity)


PhaseAxesType = TypeVar("PhaseAxesType", bound=UndulatorLockedPhaseAxes)


class Apple2(StandardReadable, Movable[Apple2Val], Generic[PhaseAxesType]):
    """Device representing the combined motor controls for an Apple2 undulator.

    Attributes:
        gap (UndulatorGap): The undulator gap motor device.
        phase (UndulatorPhaseAxes): The undulator phase axes device, consisting of four
            phase motors.

    Args:
        id_gap (UndulatorGap): An UndulatorGap device.
        id_phase (UndulatorPhaseAxes): An UndulatorPhaseAxes device.
        name (str, optional): Name of the device.
    """

    def __init__(self, id_gap: UndulatorGap, id_phase: PhaseAxesType, name=""):
        with self.add_children_as_readables():
            self.gap_ref = Reference(id_gap)
            self.phase_ref = Reference(id_phase)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, id_motor_values: Apple2Val) -> None:
        """Check ID is in a movable state and set all the demand value before moving
        them all at the same time.
        """
        gap = self.gap_ref()
        phase = self.phase_ref()
        # Only need to check gap as the phase motors share both status and gate with gap.
        await gap.raise_if_cannot_move()
        await asyncio.gather(
            phase.set_demand_positions(value=id_motor_values.extract_phase_val()),
            gap.set_demand_positions(value=float(id_motor_values.gap)),
        )
        timeout = max(await asyncio.gather(gap.get_timeout(), phase.get_timeout()))
        LOGGER.info(
            f"Moving {self.name} apple2 motors to {id_motor_values}, timeout = {timeout}"
        )
        await asyncio.gather(
            gap.set_move.set(value=1, timeout=timeout),
            phase.set_move.set(value=1, timeout=timeout),
        )
        await wait_for_value(gap.gate, UndulatorGateStatus.CLOSE, timeout=timeout)
