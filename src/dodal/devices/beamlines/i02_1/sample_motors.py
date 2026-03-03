from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class SampleMotors(StandardReadable):
    """Virtual Smaract motors on i02-1 (VMXm)."""

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        # See https://github.com/DiamondLightSource/mx-bluesky/issues/1212
        # regarding a potential motion issue with omega
        with self.add_children_as_readables():
            self.x = Motor(f"{prefix}SAMP-01:X")
            self.z = Motor(f"{prefix}SAMP-01:Z")
            self.y = Motor(f"{prefix}GONJK-01:HEIGHT")
            self.omega = Motor(f"{prefix}SAMP-01:OMEGA")
        super().__init__(name=name)
