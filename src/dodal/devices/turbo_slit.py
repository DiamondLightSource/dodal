from ophyd_async.core import Device
from ophyd_async.epics.motion.motor import Motor


class TurboSlit(Device):
    """
    This collection of motors coordinates time resolved XAS experiments.
    It selects a beam out of the polychromatic fan.
    These slits can be scanned continously or in step mode.
    The relationship between the three motors is as follows:
        - gap provides energy resolution
        - xfine selects the energy
        - arc - ???
    """

    def __init__(self, prefix: str, name: str):
        self.gap = Motor(prefix=prefix + "GAP")
        self.arc = Motor(prefix=prefix + "ARC")
        self.xfine = Motor(prefix=prefix + "XFINE")
        super().__init__(name=name)
