import numpy as np
from ophyd_async.core import Array1D, SignalR, StandardReadableFormat, soft_signal_rw
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.beamlines.device_helpers import CAM_SUFFIX
from dodal.devices.electron_analyser.abstract_analyser import (
    AbstractAnalyserDetector,
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta_region import DetectorMode


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

    def _get_energy_axis_signal(self, prefix: str = "") -> SignalR:
        """
        Override abstract and return epics signal
        """
        if hasattr(self, "energy_axis"):
            return self.energy_axis
        return epics_signal_r(Array1D[np.float64], prefix + "X_SCALE_RBV")

    def _get_angle_axis_signal(self, prefix: str = "") -> SignalR:
        """
        Override abstract and return epics signal
        """
        if hasattr(self, "angle_axis"):
            return self.angle_axis
        return epics_signal_r(Array1D[np.float64], prefix + "Y_SCALE_RBV")

    @property
    def pass_energy_type(self) -> type:
        return str


class VGScientaAnalyserDetector(AbstractAnalyserDetector[VGScientaAnalyserDriverIO]):
    def __init__(self, prefix: str, name: str):
        self.driver = VGScientaAnalyserDriverIO(prefix + CAM_SUFFIX)
        super().__init__(prefix, name, self.driver)

        self.per_scan_metadata: list[SignalR] = self.per_scan_metadata + [
            self.driver.first_x_channel,
            self.driver.x_channel_size,
            self.driver.first_y_channel,
            self.driver.y_channel_size,
            self.driver.excitation_energy_source,
            self.driver.centre_energy,
            self.driver.detector_mode,
        ]
        self.per_point_metadata: list[SignalR] = self.per_point_metadata + [
            self.driver.external_io,
        ]
