import asyncio
from dataclasses import dataclass
from functools import cached_property
from typing import Generic, TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.insertion_device.apple2_motors import (
    MotorStringSetpoint,
    UnstoppableMotorMoveLogic,
)
from dodal.devices.insertion_device.apple2_undulator_base import (
    UndulatorBase,
    estimate_motor_timeout,
    estimate_motor_timeout_from_signals,
    set_move_and_wait_for_gate,
    undulator_check_move,
)
from dodal.devices.insertion_device.enum import UndulatorGateStatus
from dodal.log import LOGGER

T = TypeVar("T")


@dataclass
class Apple2LockedPhasesVal:
    top_outer: float
    btm_inner: float


@dataclass
class Apple2PhasesVal(Apple2LockedPhasesVal):
    top_inner: float
    btm_outer: float


class UndulatorPhaseMotor(MotorStringSetpoint):
    """Phase motor that will not stop.

    Args:
        prefix (str): The setting prefix PV.
        name (str, optional): Name of the Id phase device.
    """

    def __init__(self, prefix: str, name: str = ""):
        self.user_setpoint_str = epics_signal_rw(str, prefix + "SET")
        super().__init__(f"{prefix}MTR", name=name)
        del self.motor_stop
        self.user_setpoint_readback = epics_signal_r(float, prefix + "DMD")

    @cached_property
    def movable_logic(self) -> UnstoppableMotorMoveLogic:
        return UnstoppableMotorMoveLogic(
            readback=self.user_readback,
            setpoint=self.user_setpoint,
            motor_stop=None,  # type: ignore
            low_limit_travel=self.low_limit_travel,
            high_limit_travel=self.high_limit_travel,
            dial_low_limit_travel=self.dial_low_limit_travel,
            dial_high_limit_travel=self.dial_high_limit_travel,
            velocity=self.velocity,
            acceleration_time=self.acceleration_time,
        )


Apple2PhaseValType = TypeVar("Apple2PhaseValType", bound=Apple2LockedPhasesVal)


class SafeUndulatorMoverBase(UndulatorBase, StandardReadable, Movable[T], Generic[T]):
    """Base class for movable Apple2 undulator devices using gated motion.

    Extends :class:`UndulatorBase` with the standard readable and movable
    interfaces required by ophyd-async devices.

    The move sequence is:

    * verify that the undulator is enabled and motion is permitted,
    * write the requested demand positions,
    * trigger the controller to start motion,
    * monitor the gate until motion is complete.

    Subclasses implement the device-specific demand-position handling and
    move-timeout calculation.

    Attributes:
        gate: Read-only signal indicating the current gated motion state of
            the controller.
        status: Read-only signal indicating whether the undulator is enabled.
        set_move: Signal used to trigger motion after demand positions have
            been written. Writing a value of 1 starts the move; the controller
            returns it to 0 when the move is complete.
    """

    def __init__(self, prefix: str, name: str = ""):
        self.gate = epics_signal_r(UndulatorGateStatus, prefix + "BLGATE")
        self.status = epics_signal_r(EnabledDisabledUpper, prefix + "IDBLENA")

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: T):
        LOGGER.info(f"Setting {self.name} to {value}")
        await self.set_demand_positions(value)
        timeout = await self.get_timeout()
        LOGGER.info(f"Moving {self.name} to {value} with timeout = {timeout}")
        await set_move_and_wait_for_gate(self.gate, self.set_move, timeout)


class UndulatorLockedPhaseAxes(SafeUndulatorMoverBase[Apple2PhaseValType]):
    """Two phase Motor to make up the locked id phase motion."""

    def __init__(
        self,
        prefix: str,
        top_outer: str,
        btm_inner: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.top_outer = UndulatorPhaseMotor(prefix=f"{prefix}BL{top_outer}")
            self.btm_inner = UndulatorPhaseMotor(prefix=f"{prefix}BL{btm_inner}")
        # Nothing move until this is set to 1 and it will return to 0 when done.
        self.set_move = epics_signal_w(int, f"{prefix}BL{top_outer}" + "MOVE")
        self.axes = [self.top_outer, self.btm_inner]
        super().__init__(prefix, name)

    async def set_demand_positions(self, value: Apple2PhaseValType) -> None:
        await asyncio.gather(
            self.top_outer.user_setpoint.set(value=value.top_outer),
            self.btm_inner.user_setpoint.set(value=value.btm_inner),
        )

    async def check_value(self, value: Apple2PhaseValType) -> None:
        await undulator_check_move(self.status, self.gate)
        await asyncio.gather(
            self.top_outer.check_value(value.top_outer),
            self.btm_inner.check_value(value.btm_inner),
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

    async def check_value(self, value: Apple2PhasesVal) -> None:
        await undulator_check_move(self.status, self.gate)
        await asyncio.gather(
            self.top_outer.check_value(value=value.top_outer),
            self.top_inner.check_value(value=value.top_inner),
            self.btm_inner.check_value(value=value.btm_inner),
            self.btm_outer.check_value(value=value.btm_outer),
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
        with self.add_children_as_readables():
            self.jaw_phase = UndulatorPhaseMotor(prefix=f"{prefix}BL{jaw_phase}")
        self.set_move = epics_signal_w(int, f"{prefix}BL{move_pv}" + "MOVE")
        super().__init__(prefix, name)

    async def set_demand_positions(self, value: float) -> None:
        await self.jaw_phase.user_setpoint.set(value=value)

    async def check_value(self, value: float) -> None:
        await undulator_check_move(self.status, self.gate)
        await self.jaw_phase.check_value(value=value)

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
