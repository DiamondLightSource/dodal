from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class BaseTable(StandardReadable):
    """Base class for a table with two motors representing gaps in X and Y directions."""

    def __init__(
        self,
        prefix: str,
        x: str = "X",
        y: str = "Y",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.x = Motor(prefix + x)
            self.y = Motor(prefix + y)
        super().__init__(name=name)


class PitchedBaseTable(BaseTable):
    """Base class for a table with two motors representing gaps in X and Y directions, with additional motors for pitch."""

    def __init__(
        self,
        prefix: str,
        x: str = "X",
        y: str = "Y",
        pitch: str = "PITCH",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.pitch = Motor(prefix + pitch)
        super().__init__(prefix=prefix, x=x, y=y, name=name)
