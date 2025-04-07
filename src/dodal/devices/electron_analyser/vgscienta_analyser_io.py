from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.abstract_analyser_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta_region import (
    DetectorMode,
)


class VGScientaAnalyserDriverIO(AbstractAnalyserDriverIO):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.centre_energy = epics_signal_rw(float, prefix + "CENTRE_ENERGY")
            self.first_x_channel = epics_signal_rw(int, prefix + "MinX")
            self.first_y_channel = epics_signal_rw(int, prefix + "MinY")
            self.x_channel_size = epics_signal_rw(int, prefix + "SizeX")
            self.y_channel_size = epics_signal_rw(int, prefix + "SizeY")
            self.detector_mode = epics_signal_rw(DetectorMode, prefix + "DETECTOR_MODE")
            self.image_mode = epics_signal_rw(str, prefix + "ImageMode")

        super().__init__(prefix, name)
