import asyncio
from dataclasses import dataclass
from functools import cached_property

from bluesky.protocols import Flyable, Preparable
from ophyd_async.core import (
    AsyncStatus,
    FlyMotorInfo,
    SignalR,
    SignalRW,
    SignalW,
    StandardReadableFormat,
    TimeoutCalculator,
    WatchableAsyncStatus,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.insertion_device.apple2_motors import (
    MotorStringSetpoint,
    UnstoppableMotorMoveLogic,
)
from dodal.devices.insertion_device.apple2_undulator_base import (
    SafeUndulatorMoverBase,
    estimate_motor_timeout,
    estimate_motor_timeout_from_signals,
    set_move_and_wait_for_gate,
    undulator_check_move,
)
from dodal.devices.insertion_device.enum import UndulatorGateStatus


@dataclass
class UndulatorGapMoveLogic(UnstoppableMotorMoveLogic):
    """Move logic for the Apple2 undulator gap motor.

    Extends the standard motor move logic with Apple2-specific behaviour,
    including gate/status checks, timeout estimation using the dedicated gap
    velocity PV, and triggering motion via the undulator move PV.
    """

    gate: SignalR[UndulatorGateStatus]
    status: SignalR[EnabledDisabledUpper]
    set_move: SignalW[int]
    velocity: SignalRW[float]

    async def calculate_timeout(
        self, old_position: float, new_position: float
    ) -> float:
        velocity = await self.velocity.get_value()
        return estimate_motor_timeout(new_position, old_position, velocity)

    async def check_move(self, new_position: float) -> None:
        await undulator_check_move(self.status, self.gate)
        # Check motor is within limits
        await super().check_move(new_position)

    async def move(self, new_position: float, timeout: TimeoutCalculator) -> None:
        await self.setpoint.set(new_position, timeout=timeout())
        await set_move_and_wait_for_gate(self.gate, self.set_move, timeout())


class UndulatorGapMotor(MotorStringSetpoint):
    """Motor record wrapper for the Apple2 undulator gap.

    This class adapts the standard EPICS motor interface to match the Apple2
    controller by:

    * exposing the string-valued setpoint as a float signal,
    * using the dedicated gap velocity PV,
    * disabling stopping,
    * providing Apple2-specific move logic.
    """

    def __init__(self, prefix: str, gate, status, set_move, name: str = ""):
        super().__init__(prefix=prefix, name=name)
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
            low_limit_travel=self.low_limit_travel,
            high_limit_travel=self.high_limit_travel,
            dial_low_limit_travel=self.dial_low_limit_travel,
            dial_high_limit_travel=self.dial_high_limit_travel,
            velocity=self.velocity,
            acceleration_time=self.acceleration_time,
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


class UndulatorGap(SafeUndulatorMoverBase[float], Flyable, Preparable):
    """Apple2 undulator gap device.

    Wraps an internal :class:`UndulatorGapMotor` and exposes the Apple2
    controller interface, where demand positions are written separately from
    triggering motion via a dedicated move PV.

    Supports standard moves as well as fly scanning.

    Args:
        prefix: Beamline-specific PV prefix.
        name: Device name.
    """

    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix=prefix, name=name)
        self.set_move = epics_signal_rw(int, prefix + "BLGSETP")
        with self.add_children_as_readables():
            self.motor = UndulatorGapMotor(
                prefix, self.gate, self.status, self.set_move
            )

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

    @AsyncStatus.wrap
    async def kickoff(self):
        await self.motor.kickoff()

    def complete(self) -> WatchableAsyncStatus:
        return self.motor.complete()
