
from enum import Enum

from bluesky.protocols import Configurable, Movable, Stageable
from ophyd_async.core import AsyncStatus, Device, Signal, StandardReadable


class StandardMovable(Device, Movable, Configurable, Stageable):
    pass


class TestDetector(StandardReadable):
    pass


class ControlEnum(str, Enum):
    value1 = "close"
    value2 = "open"


class TurboSlit(StandardMovable):
    """
    todo for now only the x motor
    add soft limits
    check min speed
    set speed back to before movement
    """

    motor_x = Signal(
        "BL20J-OP-PCHRO-01:TS:XFINE", # type: ignore
        0.01
    )

    def set(self, position: str) -> AsnycStatus:
        pass
        # status = self.motor_x.set(position)
        # return status


class AsyncTurboSlit(Device):
    # .val - set value channel
    # .rbv - readback value - read channel
    pass
    # motor_x = Motor()