import abc
import asyncio
from dataclasses import dataclass
from functools import cached_property
from typing import Generic, TypeVar

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    FlyMotorInfo,
    MovableLogic,
    Reference,
    SignalR,
    SignalRW,
    SignalW,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_rw,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw
from ophyd_async.epics.motor import Motor, MotorMoveLogic

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.insertion_device.enum import UndulatorGateStatus
from dodal.log import LOGGER

T = TypeVar("T")

DEFAULT_MOTOR_MIN_TIMEOUT = 10


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


async def estimate_motor_timeout_from_sigs(
    current_pos: SignalR, new_pos: SignalR, velocity: SignalR
):
    vel = await velocity.get_value()
    cur_pos = await current_pos.get_value()
    target_pos = float(await new_pos.get_value())
    return abs((target_pos - cur_pos) * 2.0 / vel) + DEFAULT_MOTOR_MIN_TIMEOUT


def estimate_motor_timeout(
    current_pos: float, new_pos: float, velocity: float
) -> float:
    return abs((new_pos - current_pos) * 2.0 / velocity) + DEFAULT_MOTOR_MIN_TIMEOUT


class UndulatorBase(abc.ABC, Generic[T]):
    """Abstract base class for Apple2 undulator devices.
    This class provides common functionality for undulator devices, including
    gate and status signal management, safety checks before motion, and abstract
    methods for setting demand positions and estimating move timeouts.
    """

    def __init__(self):
        # Gate keeper open when move is requested, closed when move is completed
        self.gate: SignalR[UndulatorGateStatus]
        self.status: SignalR[EnabledDisabledUpper]

    @abc.abstractmethod
    async def set_demand_positions(self, value: T) -> None:
        """Set the demand positions on the device without actually hitting move."""

    @abc.abstractmethod
    async def get_timeout_for_apple2(self) -> float:
        """Get the timeout for the move based on an estimate of how long it will take."""

    async def raise_if_cannot_move(self) -> None:
        if await self.status.get_value() is EnabledDisabledUpper.DISABLED:
            raise RuntimeError(f"{self.status.name} is DISABLED and cannot move.")
        if await self.gate.get_value() is UndulatorGateStatus.OPEN:
            raise RuntimeError(f"{self.status.name} is already in motion.")


class SafeUndulatorMover(StandardReadable, UndulatorBase, Generic[T]):
    """A device that will check it's safe to move the undulator before moving it and
    wait for the undulator to be safe again before calling the move complete.
    """

    def __init__(self, set_move: SignalW, prefix: str, name: str = ""):
        # Gate keeper open when move is requested, closed when move is completed
        self.gate = epics_signal_r(UndulatorGateStatus, prefix + "BLGATE")
        self.status = epics_signal_r(EnabledDisabledUpper, prefix + "IDBLENA")
        self.set_move = set_move
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: T) -> None:
        LOGGER.info(f"Setting {self.name} to {value}")
        await self.raise_if_cannot_move()
        await self.set_demand_positions(value)
        timeout = await self.get_timeout_for_apple2()
        LOGGER.info(f"Moving {self.name} to {value} with timeout = {timeout}")
        await self.set_move.set(value=1, timeout=timeout)
        await wait_for_value(self.gate, UndulatorGateStatus.CLOSE, timeout=timeout)


@dataclass
class UnstoppableMotorMoveLogic(MotorMoveLogic):
    async def stop(self):
        """Request to stop moving."""
        LOGGER.warning(f"Stopping {self.readback.name} is not supported.")


class UnstoppableMotor(Motor):
    """A motor that does not support stop."""

    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix=prefix, name=name)
        del self.motor_stop  # Remove motor_stop from the public interface

    @cached_property
    def movable_logic(self) -> MovableLogic:
        return UnstoppableMotorMoveLogic(
            readback=self.user_readback,
            setpoint=self.user_setpoint,
            # Safe to do, stop method no longer calls stop signal in movable logic.
            motor_stop=None,  # type: ignore
            low_limit_travel=self.low_limit_travel,
            high_limit_travel=self.high_limit_travel,
            dial_low_limit_travel=self.dial_low_limit_travel,
            dial_high_limit_travel=self.dial_high_limit_travel,
            velocity=self.velocity,
            acceleration_time=self.acceleration_time,
        )


@dataclass
class GapSafeMotorMoveLogic(UnstoppableMotorMoveLogic, UndulatorBase[float]):
    gate: SignalR[UndulatorGateStatus]
    status: SignalR[EnabledDisabledUpper]
    set_move: SignalW[int]

    async def check_move(self, new_position: float) -> None:
        await super().check_move(new_position)
        await self.raise_if_cannot_move()

    async def move(self, new_position: float, timeout: float | None) -> None:
        await self.set_demand_positions(new_position)
        await self.set_move.set(1, timeout=timeout)

        await wait_for_value(
            self.gate,
            UndulatorGateStatus.CLOSE,
            timeout=timeout,
        )

    async def calculate_timeout(
        self, old_position: float, new_position: float
    ) -> float:
        vel = await self.velocity.get_value()
        return estimate_motor_timeout(old_position, new_position, vel)

    async def get_timeout_for_apple2(self) -> float:
        return await estimate_motor_timeout_from_sigs(
            self.readback, self.setpoint, self.velocity
        )

    async def set_demand_positions(self, value: float) -> None:
        await self.setpoint.set(value)


class UserSetpointWrapperUnstoppableMotor(UnstoppableMotor):
    """Replace the motor setpoint with a derived signal user_setpoint. Used when the raw
    underlying signal is a str rather than a float and the conversion is handled via
    the derived signal so it works seemlessly like a normal motor using float. This
    allows for plans and devices interacting with this device not needing to worry about
    type checking or converting the values.
    """

    user_setpoint_str: SignalRW[str]

    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, name)
        self.user_setpoint = derived_signal_rw(
            self._get_setpoint, self._set_setpoint, setpoint_str=self.user_setpoint_str
        )

    async def _set_setpoint(self, value: float) -> None:
        await self.user_setpoint_str.set(str(value))

    def _get_setpoint(self, setpoint_str: str) -> float:
        return float(setpoint_str)


class GapSafeMotorNoStop(UserSetpointWrapperUnstoppableMotor):
    """Update gap safe motor that checks it's safe to move before moving."""

    def __init__(self, set_move: SignalW[int], prefix: str, name: str = ""):
        # Gate keeper open when move is requested, closed when move is completed
        self.gate = epics_signal_r(UndulatorGateStatus, prefix + "BLGATE")
        self.status = epics_signal_r(EnabledDisabledUpper, prefix + "IDBLENA")
        self.set_move = set_move
        super().__init__(prefix=prefix + "BLGAPMTR", name=name)


class UndulatorGap(GapSafeMotorNoStop, UndulatorBase):
    """Apple 2 undulator gap motor device. With PV corrections.

    Args:
        prefix (str): Beamline specific part of the PV
        name (str): Name of the Id device
    """

    def __init__(self, prefix: str, name: str = ""):
        self.set_move = epics_signal_rw(int, prefix + "BLGSETP")
        # Nothing move until this is set to 1 and it will return to 0 when done.

        self.user_setpoint_str = epics_signal_rw(str, prefix + "BLGSET")
        super().__init__(self.set_move, prefix, name)

        self.max_velocity = epics_signal_r(float, prefix + "BLGSETVEL.HOPR")
        self.min_velocity = epics_signal_r(float, prefix + "BLGSETVEL.LOPR")

        """ Clear the motor config_signal as we need new PV for velocity."""
        self._describe_config_funcs = ()
        self._read_config_funcs = ()
        self.velocity = epics_signal_rw(float, prefix + "BLGSETVEL")
        self.add_readables(
            [self.velocity, self.motor_egu, self.offset],
            format=StandardReadableFormat.CONFIG_SIGNAL,
        )

    @AsyncStatus.wrap
    async def prepare(self, value: FlyMotorInfo) -> None:
        """Prepare for a fly scan by moving to the run-up position at max velocity.
        Stores fly info for later use in kickoff.
        """
        max_velocity, min_velocity, egu = await asyncio.gather(
            self.max_velocity.get_value(),
            self.min_velocity.get_value(),
            self.motor_egu.get_value(),
        )
        velocity = abs(value.velocity)
        if not (min_velocity <= velocity <= max_velocity):
            raise ValueError(
                f"Requested velocity {velocity} {egu}/s is out of bounds: "
                f"must be between {min_velocity} and {max_velocity} {egu}/s."
            )
        await super().prepare(value)

    async def get_timeout_for_apple2(self) -> float:
        return await self.movable_logic.get_timeout_for_apple2()

    async def set_demand_positions(self, value: float) -> None:
        return await self.movable_logic.set_demand_positions(value)

    @cached_property
    def movable_logic(self) -> GapSafeMotorMoveLogic:
        return GapSafeMotorMoveLogic(
            readback=self.user_readback,
            setpoint=self.user_setpoint,
            low_limit_travel=self.low_limit_travel,
            high_limit_travel=self.high_limit_travel,
            motor_stop=None,  # type: ignore
            dial_low_limit_travel=self.dial_low_limit_travel,
            dial_high_limit_travel=self.dial_high_limit_travel,
            velocity=self.velocity,
            acceleration_time=self.acceleration_time,
            gate=self.gate,
            status=self.status,
            set_move=self.set_move,
        )


class UndulatorPhaseMotor(UserSetpointWrapperUnstoppableMotor):
    """Phase motor that will not stop.

    Args:
        prefix (str): The setting prefix PV.
        name (str, optional): Name of the Id phase device.
    """

    def __init__(self, prefix: str, name: str = ""):
        motor_pv = f"{prefix}MTR"
        self.user_setpoint_str = epics_signal_rw(str, prefix + "SET")
        self.user_setpoint_readback = epics_signal_r(float, prefix + "DMD")
        super().__init__(prefix=motor_pv, name=name)


Apple2PhaseValType = TypeVar("Apple2PhaseValType", bound=Apple2LockedPhasesVal)


class UndulatorLockedPhaseAxes(SafeUndulatorMover[Apple2PhaseValType]):
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
        super().__init__(self.set_move, prefix, name)

    async def set_demand_positions(self, value: Apple2PhaseValType) -> None:
        await asyncio.gather(
            self.top_outer.user_setpoint.set(value.top_outer),
            self.btm_inner.user_setpoint.set(value.btm_inner),
        )

    async def get_timeout_for_apple2(self) -> float:
        """Get all motor speed, current positions and target positions to calculate
        required timeout.
        """
        timeouts = await asyncio.gather(
            *[
                estimate_motor_timeout_from_sigs(
                    axis.user_readback,
                    axis.user_setpoint_readback,
                    axis.velocity,
                )
                for axis in self.axes
            ]
        )
        """A 2.0 multiplier is required to prevent premature motor timeouts in phase
        axes as it is a master-slave system, where the slave's movement,
        being dependent on the master, can take up to twice as long to complete."""
        return np.max(timeouts) * 2.0


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
            self.top_outer.user_setpoint.set(value.top_outer),
            self.top_inner.user_setpoint.set(value.top_inner),
            self.btm_inner.user_setpoint.set(value.btm_inner),
            self.btm_outer.user_setpoint.set(value.btm_outer),
        )


class UndulatorJawPhase(SafeUndulatorMover[float]):
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
        # Nothing move until this is set to 1 and it will return to 0 when done
        self.set_move = epics_signal_rw(int, f"{prefix}BL{move_pv}" + "MOVE")

        super().__init__(self.set_move, prefix, name)

    async def set_demand_positions(self, value: float) -> None:
        await self.jaw_phase.user_setpoint.set(value)

    # async def get_timeout_for_apple2(self) -> float:
    #     """Get motor speed, current position and target position to calculate required
    #     timeout.
    #     """
    #     return await estimate_motor_timeout(
    #         self.jaw_phase.user_setpoint_readback,
    #         self.jaw_phase.user_readback,
    #         self.jaw_phase.velocity,
    #     )

    async def get_timeout_for_apple2(self) -> float:
        """Get motor speed, current position and target position to calculate required
        timeout.
        """
        readback, setpoint = await asyncio.gather(
            self.jaw_phase.user_readback.get_value(),
            self.jaw_phase.user_setpoint_readback.get_value(),
        )
        return await self.jaw_phase.movable_logic.calculate_timeout(readback, setpoint)


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
            self.gap = Reference(id_gap)
            self.phase = Reference(id_phase)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, id_motor_values: Apple2Val) -> None:
        """Check ID is in a movable state and set all the demand value before moving
        them all at the same time.
        """
        # Only need to check gap as the phase motors share both status and gate with gap.
        await self.gap().movable_logic.raise_if_cannot_move()

        await asyncio.gather(
            self.phase().set_demand_positions(
                value=id_motor_values.extract_phase_val()
            ),
            self.gap().set_demand_positions(id_motor_values.gap),
        )
        timeout = np.max(
            await asyncio.gather(
                self.gap().get_timeout_for_apple2(),
                self.phase().get_timeout_for_apple2(),
            )
        )
        LOGGER.info(
            f"Moving {self.name} apple2 motors to {id_motor_values}, timeout = {timeout}"
        )
        await asyncio.gather(
            self.gap().set_move.set(value=1, timeout=timeout),
            self.phase().set_move.set(value=1, timeout=timeout),
        )

        await wait_for_value(
            self.gap().gate, UndulatorGateStatus.CLOSE, timeout=timeout
        )
