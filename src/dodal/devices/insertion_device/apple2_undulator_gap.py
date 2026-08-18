import asyncio
from dataclasses import dataclass
from functools import cached_property

from ophyd_async.core import (
    FlyMotorInfo,
    SignalR,
    SignalW,
    StandardReadableFormat,
    TimeoutCalculator,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w
from ophyd_async.epics.motor import MotorFlyCtx

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.insertion_device.apple2_motors import (
    MotorStringSetpoint,
    UnstoppableMotorFlyableMoveLogic,
)
from dodal.devices.insertion_device.apple2_undulator_base import (
    UndulatorBase,
    estimate_motor_timeout,
    estimate_motor_timeout_from_signals,
    set_move_and_wait_for_gate,
    undulator_check_move,
)
from dodal.devices.insertion_device.enum import UndulatorGateStatus


@dataclass
class UndulatorGapFlyableMoveLogic(UnstoppableMotorFlyableMoveLogic):
    """Move logic for the Apple2 undulator gap motor.

    Extends the standard motor move logic with Apple2-specific behaviour,
    including gate/status checks, timeout estimation using the dedicated gap
    velocity PV, and triggering motion via the undulator move PV.
    """

    gate: SignalR[UndulatorGateStatus]
    status: SignalR[EnabledDisabledUpper]
    set_move: SignalW[int]
    min_velocity: SignalR[float]

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

    async def on_prepare(self, value: FlyMotorInfo) -> MotorFlyCtx:
        max_velocity, min_velocity, egu = await asyncio.gather(
            self.max_velocity.get_value(),
            self.min_velocity.get_value(),
            self.motor_egu.get_value(),
        )
        velocity = abs(value.speed)
        if not (min_velocity <= velocity <= max_velocity):
            raise ValueError(
                f"Requested velocity {velocity} {egu}/s is out of bounds: "
                f"must be between {min_velocity} and {max_velocity} {egu}/s."
            )
        return await super().on_prepare(value)


class UndulatorGap(MotorStringSetpoint, UndulatorBase[float]):
    """EPICS motor interface for the Apple2 undulator gap.

    Adapts the standard EPICS motor interface to the Apple2 undulator
    controller, where the gap setpoint is written as a string and motion is
    started separately via the controller's move signal.

    The Apple2-specific interface:

    * exposes the string-valued controller setpoint as a float motor
      setpoint,
    * uses the dedicated Apple2 gap velocity PV,
    * disables the standard motor stop signal because the gap cannot be
      stopped once motion has started,
    * uses the Apple2 gate and enable status signals to control motion.
    """

    def __init__(self, prefix: str, name: str = ""):
        self.user_setpoint_str = epics_signal_rw(str, prefix + "BLGSET")
        super().__init__(prefix + "BLGAPMTR", name=name)
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
        del self.motor_stop

        self.gate = epics_signal_r(UndulatorGateStatus, prefix + "BLGATE")
        self.status = epics_signal_r(EnabledDisabledUpper, prefix + "IDBLENA")
        self.set_move = epics_signal_w(int, prefix + "BLGSETP")

    @cached_property
    def _logic(self) -> UndulatorGapFlyableMoveLogic:
        return UndulatorGapFlyableMoveLogic(
            readback=self.user_readback,
            setpoint=self.user_setpoint,
            motor_stop=None,  # type: ignore
            low_limit_travel=self.low_limit_travel,
            high_limit_travel=self.high_limit_travel,
            dial_low_limit_travel=self.dial_low_limit_travel,
            dial_high_limit_travel=self.dial_high_limit_travel,
            velocity=self.velocity,
            max_velocity=self.max_velocity,
            min_velocity=self.min_velocity,
            motor_egu=self.motor_egu,
            acceleration_time=self.acceleration_time,
            motor_done_move=self.motor_done_move,
            # Specific to this class.
            gate=self.gate,
            status=self.status,
            set_move=self.set_move,
        )

    async def set_demand_positions(self, value: float) -> None:
        await self.user_setpoint.set(value)

    async def get_timeout(self) -> float:
        return await estimate_motor_timeout_from_signals(
            self.user_setpoint, self.user_readback, self.velocity
        )
