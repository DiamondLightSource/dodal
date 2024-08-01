from ophyd_async.core import StandardReadable
from ophyd_async.epics.motion import Motor


class Slits(StandardReadable):
    """
    Representation of a 4-blade set of slits. Allows control/readout of the gap
    between each pair of blades.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x_gap = Motor(prefix + "X:SIZE")
            self.y_gap = Motor(prefix + "Y:SIZE")
            self.x_centre = Motor(prefix + "X:CENTRE")
            self.y_centre = Motor(prefix + "Y:CENTRE")
        super().__init__(name)


class SpecialSlitsi22(StandardReadable):
    """
    these are unlikely to be moved during a scan
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x = Motor(prefix + "X:RBV")
            self.y = Motor(prefix + "Y:RBV")
            self.horizontal_dso = Motor(prefix + "HDSO:RBV")
            self.vertical_dso = Motor(prefix + "VDSO:RBV")
        super().__init__(name)
