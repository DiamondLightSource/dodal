from ophyd_async.core import StandardReadable, StrictEnum, SubsetEnum
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


class FilterWheel(StandardReadable):
    def __init__(
        self,
        prefix: str,
        filter_infix: str,
        filter_selections: type[StrictEnum | SubsetEnum],
        name: str = "",
    ):
        filter_prefix: str = f"{prefix}{filter_infix}"
        with self.add_children_as_readables():
            self.user_setpoint = epics_signal_rw(
                datatype=filter_selections,
                read_pv=filter_prefix,
                write_pv=filter_prefix,
            )
        super().__init__(name=name)
