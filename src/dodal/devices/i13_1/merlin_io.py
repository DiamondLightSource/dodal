from ophyd_async.core import StrictEnum
from ophyd_async.epics import adcore
from ophyd_async.epics.core import epics_signal_rw_rbv


class MerlinImageMode(StrictEnum):
    SINGLE = "Single"
    MULTIPLE = "Multiple"
    CONTINUOUS = "Continuous"
    THRESHOLD = "Threshold"
    BACKGROUND = "Background"


class MerlinDriverIO(adcore.ADBaseIO):
    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(prefix, name=name)
        self.image_mode = epics_signal_rw_rbv(MerlinImageMode, prefix + "ImageMode")
