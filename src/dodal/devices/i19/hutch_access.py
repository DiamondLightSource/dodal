from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r


class HutchAccessControl(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.active_hutch = epics_signal_r(str, f"{prefix}EHStatus.VALA")
        super().__init__(name)
