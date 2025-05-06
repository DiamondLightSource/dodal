import numpy as np
from ophyd_async.core import Array1D, SignalR, StandardReadableFormat, soft_signal_rw
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.abstract_analyser_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract_detector import (
    AbstractElectronAnalyserDetector,
    AbstractElectronAnalyserRegionDetector,
)
from dodal.devices.electron_analyser.vgscienta_region import (
    DetectorMode,
    VGScientaRegion,
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


class VGScientaRegionDetector(
    AbstractElectronAnalyserRegionDetector[VGScientaAnalyserDriverIO, VGScientaRegion]
):
    def configure_region(self):
        # ToDo - Need to move configure plans to here and rewrite tests
        pass


class VGScientaDetector(
    AbstractElectronAnalyserDetector[
        VGScientaAnalyserDriverIO, VGScientaSequence, VGScientaRegion
    ]
):
    def load_sequence(self, filename: str) -> VGScientaSequence:
        return load_json_file_to_class(VGScientaSequence, filename)

    def _create_region_detector(
        self, driver: VGScientaAnalyserDriverIO, region: VGScientaRegion
    ) -> VGScientaRegionDetector:
        return VGScientaRegionDetector(self.name, driver, region)
