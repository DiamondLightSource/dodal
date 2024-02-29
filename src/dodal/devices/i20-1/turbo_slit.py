from ophyd import Component, Device, EpicsSignal, StatusBase


class TurboSlit(Device):
    """
    todo for now only the x motor
    - direct movement 
    - continuous movement
    - continuous movement with a defined trajectory
    - trajectory scan - with TTL signal from Zebra box
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
