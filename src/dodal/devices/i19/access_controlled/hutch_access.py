from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r

ACCESS_DEVICE_NAME = "access_control"  # Device name in i19-blueapi


class HutchAccessControl(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.active_hutch = epics_signal_r(str, f"{prefix}EHStatus.VALA")
        super().__init__(name)
