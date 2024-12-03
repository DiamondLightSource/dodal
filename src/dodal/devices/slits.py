from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class MinimalSlits(StandardReadable):
    """Gap only X Y slits."""

    def __init__(
        self,
        prefix: str,
        suffix: tuple[str, str] = ("X:SIZE", "Y:SIZE"),
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.x_gap = Motor(prefix + suffix[0])
            self.y_gap = Motor(prefix + suffix[1])
        super().__init__(name=name)


class Slits(MinimalSlits):
    """
    Representation of a 4-blade set of slits. Allows control/readout of the gap
    between each pair of blades.
    """

    def __init__(
        self,
        prefix: str,
        suffix: tuple[str, str, str, str] = (
            "X:SIZE",
            "Y:SIZE",
            "X:CENTRE",
            "Y:CENTRE",
        ),
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.x_centre = Motor(prefix + suffix[2])
            self.y_centre = Motor(prefix + suffix[3])
        super().__init__(prefix=prefix, suffix=suffix[0:2], name=name)


class FullSlits(Slits):
    """XY slits with each blade/aperture movable independently"""

    def __init__(
        self,
        prefix: str,
        suffix: tuple[str, str, str, str, str, str, str, str] = (
            "X:SIZE",
            "Y:SIZE",
            "X:CENTRE",
            "Y:CENTRE",
            "X:RING",
            "X:HALL",
            "Y:PLUS",
            "Y:MINUS",
        ),
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.x_ring = Motor(prefix + suffix[4])
            self.x_hall = Motor(prefix + suffix[5])
            self.y_top = Motor(prefix + suffix[6])
            self.y_bot = Motor(prefix + suffix[7])
        super().__init__(prefix=prefix, suffix=suffix[0:4], name=name)
