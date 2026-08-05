import asyncio
from dataclasses import dataclass
from functools import cached_property

from ophyd_async.core import (
    AsyncStatus,
    FlyMotorInfo,
    MovableLogic,
    SignalR,
    SignalRW,
    SignalW,
    StandardReadableFormat,
    TimeoutCalculator,
    derived_signal_rw,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw
from ophyd_async.epics.motor import Motor, MotorMoveLogic

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.insertion_device.apple2_undulator_base import (
    SafeUndulatorMoverBase,
    estimate_motor_timeout,
    estimate_motor_timeout_from_signals,
    set_move_and_wait_for_gate,
    undulator_check_move,
)
from dodal.devices.insertion_device.enum import UndulatorGateStatus
from dodal.log import LOGGER


def create_user_setpoint_str(prefix: str) -> tuple[SignalRW[str], SignalRW[float]]:
    async def _set_user_setpoint(value: float) -> None:
        await user_setpoint_str.set(str(value))

    def _read_user_setpoint(setpoint: str) -> float:
        return float(setpoint)

    user_setpoint_str = epics_signal_rw(str, prefix + "SET")
    user_setpoint = derived_signal_rw(
        _read_user_setpoint,
        _set_user_setpoint,
        setpoint=user_setpoint_str,
    )
    return user_setpoint_str, user_setpoint


@dataclass
class UndulatorGapMoveLogic(MovableLogic[float]):
    gate: SignalR[UndulatorGateStatus]
    status: SignalR[EnabledDisabledUpper]
    set_move: SignalW[int]
    velocity: SignalRW[float]

    async def calculate_timeout(
        self, old_position: float, new_position: float
    ) -> float:
        velocity = await self.velocity.get_value()
        return estimate_motor_timeout(new_position, old_position, velocity)

    async def stop(self) -> None:
        LOGGER.warning(f"Stopping {self.readback.name} is not supported.")

    async def check_move(self, new_position: float) -> None:
        await undulator_check_move(self.status, self.gate)

    async def move(self, new_position: float, timeout: TimeoutCalculator) -> None:
        await self.setpoint.set(new_position, timeout=timeout())
        await set_move_and_wait_for_gate(self.gate, self.set_move, timeout())


class UndulatorGapMotor(Motor):
    def __init__(self, prefix: str, gate, status, set_move, name: str = ""):
        super().__init__(prefix=prefix, name=name)
        self.user_setpoint_str, self.user_setpoint = create_user_setpoint_str(prefix)
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
        # Motor is unstoppable.
        self.motor_stop = None
        self._movable_logic = UndulatorGapMoveLogic(
            readback=self.user_readback,
            setpoint=self.user_setpoint,
            motor_stop=self.motor_stop,  # type: ignore
            velocity=self.velocity,
            # Specific to this class.
            gate=gate,
            status=status,
            set_move=set_move,
        )

    @cached_property
    def movable_logic(self) -> UndulatorGapMoveLogic:
        return self._movable_logic

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


class UndulatorGap(SafeUndulatorMoverBase[float]):
    """Apple 2 undulator gap motor device. With PV corrections.

    Args:
        prefix (str): Beamline specific part of the PV
        name (str): Name of the Id device
    """

    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix=prefix, name=name)
        # Nothing move until this is set to 1 and it will return to 0 when done.
        self.set_move = epics_signal_rw(int, prefix + "BLGSETP")
        self.motor = UndulatorGapMotor(prefix, self.gate, self.status, self.set_move)

    async def set_demand_positions(self, value: float) -> None:
        await self.motor.user_setpoint.set(value)

    async def get_timeout(self) -> float:
        return await estimate_motor_timeout_from_signals(
            self.motor.user_setpoint, self.motor.user_readback, self.motor.velocity
        )

    @AsyncStatus.wrap
    async def prepare(self, value: FlyMotorInfo) -> None:
        """Prepare for a fly scan by moving to the run-up position at max velocity.
        Stores fly info for later use in kickoff.
        """
        await self.motor.prepare(value)


@dataclass
class UnstoppableMotorMoveLogic(MotorMoveLogic):
    async def stop(self):
        """Request to stop moving."""
        LOGGER.warning(f"Stopping {self.readback.name} is not supported.")


class UndulatorPhaseMotor(Motor):
    """Phase motor that will not stop.

    Args:
        prefix (str): The setting prefix PV.
        name (str, optional): Name of the Id phase device.
    """

    def __init__(self, prefix: str, name: str = ""):
        motor_pv = f"{prefix}MTR"
        super().__init__(prefix=motor_pv, name=name)
        self.user_setpoint_str, self.user_setpoint = create_user_setpoint_str(prefix)
        self.user_setpoint_readback = epics_signal_r(float, prefix + "DMD")

    @cached_property
    def movable_logic(self) -> UnstoppableMotorMoveLogic:
        """The combined move + fly logic, shared by movable_logic and flyable_logic."""
        return UnstoppableMotorMoveLogic(
            readback=self.user_readback,
            setpoint=self.user_setpoint,
            # Safe to do, stop method no longer calls stop signal in movable logic.
            motor_stop=self.motor_stop,  # type: ignore
            low_limit_travel=self.low_limit_travel,
            high_limit_travel=self.high_limit_travel,
            dial_low_limit_travel=self.dial_low_limit_travel,
            dial_high_limit_travel=self.dial_high_limit_travel,
            velocity=self.velocity,
            acceleration_time=self.acceleration_time,
        )
