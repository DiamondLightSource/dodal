from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.base_analyser import BaseAnalyser
from dodal.devices.electron_analyser.vgscienta.vgscienta_region import (
    DetectorMode,
)


class VGScientaAnalyser(BaseAnalyser):
    PV_CENTRE_ENERGY = "CENTRE_ENERGY"

    PV_DETECTOR_MODE = "DETECTOR_MODE"
    PV_ENERGY_STEP = "STEP_SIZE"

    PV_FIRST_X_CHANNEL = "MinX"
    PV_FIRST_Y_CHANNEL = "MinY"
    PV_LAST_X_CHANNEL = "SizeX"
    PV_LAST_Y_CHANNEL = "SizeY"
    PV_IMAGE_MODE = "ImageMode"

    def __init__(self, prefix: str, name: str = "") -> None:
        self.prefix = prefix

        with self.add_children_as_readables():
            self.centre_energy_signal = epics_signal_rw(
                float, self.prefix + VGScientaAnalyser.PV_CENTRE_ENERGY
            )
            self.first_x_channel_signal = epics_signal_rw(
                int, self.prefix + VGScientaAnalyser.PV_FIRST_X_CHANNEL
            )
            self.first_y_channel_signal = epics_signal_rw(
                int, self.prefix + VGScientaAnalyser.PV_FIRST_Y_CHANNEL
            )
            self.last_x_channel_signal = epics_signal_rw(
                int, self.prefix + VGScientaAnalyser.PV_LAST_X_CHANNEL
            )
            self.last_y_channel_signal = epics_signal_rw(
                int, self.prefix + VGScientaAnalyser.PV_LAST_Y_CHANNEL
            )
            self.detector_mode_signal = epics_signal_rw(
                DetectorMode, self.prefix + VGScientaAnalyser.PV_DETECTOR_MODE
            )
            self.energy_step_signal = epics_signal_rw(
                float, self.prefix + VGScientaAnalyser.PV_ENERGY_STEP
            )

            self.image_mode_signal = epics_signal_rw(
                str, self.prefix + VGScientaAnalyser.PV_IMAGE_MODE
            )

        super().__init__(prefix, name)
