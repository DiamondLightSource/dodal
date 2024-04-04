from ophyd_async.core import Device
from ophyd_async.epics.motion.motor import Motor


class TurboSlit(Device):
    """
    todo for now only the x motor
    add soft limits
    check min speed
    set speed back to before movement
    """

    def __init__(self, prefix: str, name: str):
        self.gap = Motor(prefix=prefix + "GAP")
        self.arc = Motor(prefix=prefix + "ARC")
        self.xfine = Motor(prefix=prefix + "XFINE")
        super().__init__(name=name)
