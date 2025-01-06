from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.attenuator.filter_selections import FilterSelection


class FilterMotor(StandardReadable):
    def __init__(
        self, prefix: str, filter_selections: type[FilterSelection], name: str = ""
    ):
        with self.add_children_as_readables():
            self.user_setpoint = epics_signal_rw(filter_selections, f"{prefix}SELECT")
        super().__init__(name=name)
