import abc
import asyncio
from dataclasses import dataclass
from functools import cached_property
from typing import Generic, TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, Reference, StandardReadable
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.insertion_device.undulator.access_control import (
    UndulatorAccessControl,
)
from dodal.devices.insertion_device.undulator.utils import (
    MotorStringSetpoint,
    UndulatorCoordinatableMove,
    UnstoppableMotorMoveLogic,
    estimate_motor_timeout_from_signals,
)
from dodal.log import LOGGER


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
        motor_pv = f"{prefix}MTR"
        self.user_setpoint_str = epics_signal_rw(str, prefix + "SET")
        super().__init__(motor_pv, name=name)
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


T = TypeVar("T")


class UndulatorPhaseAxesBase(
    abc.ABC, StandardReadable, Movable[T], UndulatorCoordinatableMove[T], Generic[T]
):
    """Base class for Apple2 undulator devices that use gated motion.

    Subclasses implement writing demand positions and estimating move
    timeouts, while this class provides the common sequence of:

    * checking that motion is permitted,
    * writing demand positions,
    * triggering the controller move,
    * waiting for motion to complete.

    Attributes:
        gate: Gate status indicating whether the controller is moving.
        status: Enable state of the undulator.
        set_move: Signal used to trigger motion after demands have been written.
    """

    def __init__(self, access_control: UndulatorAccessControl, name: str = ""):
        # Gate keeper open when move is requested, closed when move is completed
        self.access_control_ref = Reference(access_control)
        super().__init__(name=name)

    @abc.abstractmethod
    async def set_demand_positions(self, value: T) -> None:
        """Set the demand positions on the device without actually hitting move."""

    @AsyncStatus.wrap
    async def set(self, value: T):
        LOGGER.info(f"Setting {self.name} to {value}")
        await self.access_control_ref().check_value()
        await self.set_demand_positions(value)
        timeout = await self.get_timeout()
        LOGGER.info(f"Moving {self.name} to {value} with timeout = {timeout}")
        await self.access_control_ref().set_move_and_wait_for_gate(
            self.set_move, timeout
        )


class UndulatorLockedPhaseAxes(UndulatorPhaseAxesBase[Apple2PhaseValType]):
    """Two phase Motor to make up the locked id phase motion."""

    def __init__(
        self,
        prefix: str,
        top_outer: str,
        btm_inner: str,
        access_control: UndulatorAccessControl,
        name: str = "",
    ):
        # Gap demand set point and readback
        with self.add_children_as_readables():
            self.top_outer = UndulatorPhaseMotor(prefix=f"{prefix}BL{top_outer}")
            self.btm_inner = UndulatorPhaseMotor(prefix=f"{prefix}BL{btm_inner}")
        # Nothing move until this is set to 1 and it will return to 0 when done.
        self.set_move = epics_signal_rw(int, f"{prefix}BL{top_outer}" + "MOVE")
        self.axes = [self.top_outer, self.btm_inner]
        super().__init__(access_control, name)

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
        access_control: UndulatorAccessControl,
        name: str = "",
    ):
        # Gap demand set point and readback
        with self.add_children_as_readables():
            self.top_inner = UndulatorPhaseMotor(prefix=f"{prefix}BL{top_inner}")
            self.btm_outer = UndulatorPhaseMotor(prefix=f"{prefix}BL{btm_outer}")

        super().__init__(
            prefix,
            top_outer=top_outer,
            btm_inner=btm_inner,
            access_control=access_control,
            name=name,
        )
        self.axes.extend([self.top_inner, self.btm_outer])

    async def set_demand_positions(self, value: Apple2PhasesVal) -> None:
        await asyncio.gather(
            self.top_outer.user_setpoint.set(value=value.top_outer),
            self.top_inner.user_setpoint.set(value=value.top_inner),
            self.btm_inner.user_setpoint.set(value=value.btm_inner),
            self.btm_outer.user_setpoint.set(value=value.btm_outer),
        )


class UndulatorJawPhase(UndulatorPhaseAxesBase[float]):
    """A JawPhase movable, this is use for moving the jaw phase which is use to control
    the linear arbitrary polarisation but only on some of the beamline.
    """

    def __init__(
        self,
        prefix: str,
        move_pv: str,
        access_control: UndulatorAccessControl,
        jaw_phase: str = "JAW",
        name: str = "",
    ):
        # Gap demand set point and readback
        with self.add_children_as_readables():
            self.jaw_phase = UndulatorPhaseMotor(prefix=f"{prefix}BL{jaw_phase}")
        self.set_move = epics_signal_rw(int, f"{prefix}BL{move_pv}" + "MOVE")
        super().__init__(access_control, name)

    async def set_demand_positions(self, value: float) -> None:
        await self.jaw_phase.user_setpoint.set(value=value)

    async def get_timeout(self) -> float:
        """Get motor speed, current position and target position to calculate required
        timeout.
        """
        return await estimate_motor_timeout_from_signals(
            self.jaw_phase.user_setpoint_readback,
            self.jaw_phase.user_readback,
            self.jaw_phase.velocity,
        )


PhaseAxesType = TypeVar("PhaseAxesType", bound=UndulatorLockedPhaseAxes)
