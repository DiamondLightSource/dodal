from ophyd_async.core import StandardReadable, SubsetEnum
from ophyd_async.epics.core import epics_signal_rw


class FilterMotor(StandardReadable):
    def __init__(
        self, prefix: str, filter_selections: type[SubsetEnum], name: str = ""
    ):
        with self.add_children_as_readables():
            self.user_setpoint = epics_signal_rw(filter_selections, f"{prefix}SELECT")
            self.done_move = epics_signal_rw(
                int, f"{prefix}DMOV"
            )  # 1 for yes, 0 for no
        super().__init__(name=name)
