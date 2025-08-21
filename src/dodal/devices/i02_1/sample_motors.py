from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class SampleMotors(StandardReadable):
    """Virtual Smaract motors on i02-1 (VMXm)"""

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        # See https://github.com/DiamondLightSource/mx-bluesky/issues/1212
        # regarding a potential motion issue with omega
        with self.add_children_as_readables():
            self.x = Motor(f"{prefix}X")
            self.z = Motor(f"{prefix}Z")
            self.omega = Motor(f"{prefix}OMEGA")
        super().__init__(name=name)
