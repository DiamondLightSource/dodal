from ophyd_async.epics.core import epics_signal_r

from dodal.devices.motors import XYZStage


class Aperture(XYZStage):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.small = epics_signal_r(float, prefix + "Y:SMALL_CALC")
        self.medium = epics_signal_r(float, prefix + "Y:MEDIUM_CALC")
        self.large = epics_signal_r(float, prefix + "Y:LARGE_CALC")
        super().__init__(prefix, name)
