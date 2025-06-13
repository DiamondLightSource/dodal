from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


# todo replace this device using motor created in https://github.com/DiamondLightSource/dodal/pull/1277/files
class SampleMotors(StandardReadable):
    """Virtual Smaract motors on i02-1 (VMXm)"""

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.x = Motor(f"{prefix}X")
            self.z = Motor(f"{prefix}Z")
            # See https://github.com/DiamondLightSource/dodal/pull/211/files#r1404213835 if issues are seen in motion
            self.omega = Motor(f"{prefix}OMEGA")
        super().__init__(name=name)
