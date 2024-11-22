from ophyd_async.core import (
    StandardReadable,
)
from ophyd_async.epics.core import epics_signal_r


class Diode(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        self._prefix = prefix
        with self.add_children_as_readables():
            self.signal = epics_signal_r(float, prefix + "B:DIODE:I")

        super().__init__(name=name)
