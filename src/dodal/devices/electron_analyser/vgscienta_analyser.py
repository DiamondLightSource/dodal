import numpy as np
from ophyd_async.core import Array1D, SignalR, StandardReadableFormat, soft_signal_rw
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.beamlines.device_helpers import CAM_SUFFIX
from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.abstract_analyser import (
    AbstractAnalyserDriverIO,
    AbstractElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.vgscienta_region import (
    DetectorMode,
    VGScientaSequence,
)


class VGScientaAnalyserDriverIO(AbstractAnalyserDriverIO):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.excitation_energy_source = soft_signal_rw(str, initial_value=None)
            # Used for setting up region data acquisition.
            self.centre_energy = epics_signal_rw(float, prefix + "CENTRE_ENERGY")
            self.first_x_channel = epics_signal_rw(int, prefix + "MinX")
            self.first_y_channel = epics_signal_rw(int, prefix + "MinY")
            self.x_channel_size = epics_signal_rw(int, prefix + "SizeX")
            self.y_channel_size = epics_signal_rw(int, prefix + "SizeY")
            self.detector_mode = epics_signal_rw(DetectorMode, prefix + "DETECTOR_MODE")

        with self.add_children_as_readables():
            # Used to read detector data after acqusition.
            self.external_io = epics_signal_r(Array1D[np.float64], prefix + "EXTIO")

        super().__init__(prefix, name)

    def _create_energy_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        return epics_signal_r(Array1D[np.float64], prefix + "X_SCALE_RBV")

    def _create_angle_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        return epics_signal_r(Array1D[np.float64], prefix + "Y_SCALE_RBV")

    @property
    def pass_energy_type(self) -> type:
        return str


class VGScientaAnalyserDetector(
    AbstractElectronAnalyserDetector[VGScientaAnalyserDriverIO, VGScientaSequence]
):
    def __init__(self, prefix: str, name: str):
        self.driver = VGScientaAnalyserDriverIO(prefix + CAM_SUFFIX)
        super().__init__(name, self.driver)

    def get_sequence(self, filename: str) -> VGScientaSequence:
        return load_json_file_to_class(VGScientaSequence, filename)
