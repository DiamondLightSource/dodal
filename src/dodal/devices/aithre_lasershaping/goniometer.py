from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor

# goniometer and the stages it sits on


class Goniometer(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")
        self.sampy = Motor(prefix + "SAMPY")
        self.sampz = Motor(prefix + "SAMPZ")
        self.omega = Motor(prefix + "OMEGA")
        super().__init__(name)


# to create this for lab 18-21
#    GonioStages(prefix="LA18L-MO-LSR-01:")
