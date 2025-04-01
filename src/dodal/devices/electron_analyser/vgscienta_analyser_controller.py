import numpy as np
from ophyd_async.core import Array1D
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.abstract_analyser_controller import (
    AbstractAnalyserController,
)
from dodal.devices.electron_analyser.vgscienta_region import (
    DetectorMode,
)


class VGScientaAnalyserController(AbstractAnalyserController):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            # Used for setting up region data acquisition
            self.centre_energy = epics_signal_rw(float, prefix + "CENTRE_ENERGY")
            self.first_x_channel = epics_signal_rw(int, prefix + "MinX")
            self.first_y_channel = epics_signal_rw(int, prefix + "MinY")
            self.x_channel_size = epics_signal_rw(int, prefix + "SizeX")
            self.y_channel_size = epics_signal_rw(int, prefix + "SizeY")
            self.detector_mode = epics_signal_rw(DetectorMode, prefix + "DETECTOR_MODE")
            self.image_mode = epics_signal_rw(str, prefix + "ImageMode")

            # Used to read detector data after acqusition
            self.external_io = epics_signal_r(Array1D[np.float64], prefix + "EXTIO")
            self.energy_axis = epics_signal_r(
                Array1D[np.float64], prefix + "X_SCALE_RBV"
            )
            self.angle_axis = epics_signal_r(
                Array1D[np.float64], prefix + "Y_SCALE_RBV"
            )

        super().__init__(prefix, name)
