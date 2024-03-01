
from ophyd import Component, Device, EpicsSignal, StatusBase
from ophyd_async.core import Device as OphydV2Device


class TurboSlit(OphydV2Device):
    """
    todo for now only the x motor
    add soft limits
    check min speed
    set speed back to before movement
    """

    motor_x = Component(
        EpicsSignal,
        "BL20J-OP-PCHRO-01:TS:XFINE",
    )

    def set(self, position: str) -> StatusBase:
        status = self.motor_x.set(position)
        return status


class AsyncTurboSlit(Device):
    # .val - set value channel
    # .rbv - readback value - read channel
    pass
    # motor_x = Motor()