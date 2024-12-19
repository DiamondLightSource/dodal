from ophyd_async.core import StandardReadable, SubsetEnum
from ophyd_async.epics.signal import epics_signal_rw


class FilterMotor(StandardReadable):
    def __init__(
        self, filter_selections: type[SubsetEnum], prefix: str, name: str = ""
    ):
        with self.add_children_as_readables():
            self.user_setpoint = epics_signal_rw(filter_selections, prefix)
        super().__init__(name=name)
