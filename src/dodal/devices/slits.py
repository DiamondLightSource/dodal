from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class MinimalSlits(StandardReadable):
    """Gap only X Y slits."""

    def __init__(
        self,
        prefix: str,
        x_gap: str = "X:SIZE",
        y_gap: str = "Y:SIZE",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.x_gap = Motor(prefix + x_gap)
            self.y_gap = Motor(prefix + y_gap)
        super().__init__(name=name)


class Slits(MinimalSlits):
    """
    Representation of a 4-blade set of slits. Allows control/readout of the gap
    between each pair of blades.
    """

    def __init__(
        self,
        prefix: str,
        x_gap: str = "X:SIZE",
        y_gap: str = "Y:SIZE",
        x_centre: str = "X:CENTRE",
        y_centre: str = "Y:CENTRE",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.x_centre = Motor(prefix + x_centre)
            self.y_centre = Motor(prefix + y_centre)
        super().__init__(prefix=prefix, x_gap=x_gap, y_gap=y_gap, name=name)
