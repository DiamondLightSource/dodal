from enum import StrEnum

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.sim import SimMotor

from dodal.devices.i19.blueapi_device import HutchState, OpticsBlueAPIDevice


class MotorPosition(StrEnum):
    IN = "in"
    OUT = "out"


class AccessControlledEh2Device(OpticsBlueAPIDevice):
    def __init__(self, name: str = "") -> None:
        self.hutch = HutchState.EH2
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: MotorPosition):
        request_params = {
            "name": "move_motors",
            "params": {
                "experiment_hutch": self.hutch.value,
                "access_device": "access_control",
                "position": value.value,
            },
        }
        await super().set(request_params)


class FakeOpticsDevice(StandardReadable, Movable):
    def __init__(self, name: str = "") -> None:
        self.motor1 = SimMotor("m1")
        self.motor2 = SimMotor("m2")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: MotorPosition):
        if value == MotorPosition.IN:
            await self.motor1.set(1.0)
            await self.motor2.set(1.8)
        else:
            await self.motor1.set(0.0)
            await self.motor2.set(0.0)
