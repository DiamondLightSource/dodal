from enum import StrEnum

import bluesky.plan_stubs as bps
from blueapi.core import MsgGenerator
from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.sim import SimMotor

from dodal.common import inject
from dodal.devices.i19.blueapi_device import HutchState, OpticsBlueAPIDevice


class MotorPosition(StrEnum):
    IN = "IN"
    OUT = "OUT"


class AccessControlledOpticsMotors(OpticsBlueAPIDevice):
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


class FakeOpticsMotors(StandardReadable, Movable[MotorPosition]):
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


async def optics_motors(name="optics_motors") -> FakeOpticsMotors:
    motors = FakeOpticsMotors(name=name)
    await motors.connect()
    return motors


MOTOR: FakeOpticsMotors = inject("optics_motors")


def move_motors(
    position: MotorPosition, motors: FakeOpticsMotors = MOTOR
) -> MsgGenerator:
    yield from bps.abs_set(motors, position, wait=True)


# NOTE. Yeah, without access control I can't do a thing
# Need one fixture for access allowed and one for access denied
# And some way to decorate the plan? r maybe a different plan?
