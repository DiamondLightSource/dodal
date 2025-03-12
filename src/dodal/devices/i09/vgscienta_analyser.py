from bluesky.protocols import Movable
from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_w

from dodal.devices.i09.ses_region import (
    AcquisitionMode,
    DetectorMode,
    EnergyMode,
    SESRegion,
)
from dodal.log import LOGGER, do_default_logging_setup

do_default_logging_setup()


class VGScientaAnalyser(StandardReadable, Movable):
    """
    Device to configure electron analyser with new region settings.
    """

    PV_LOW_ENERGY = "LOW_ENERGY"
    PV_HIGH_ENERGY = "HIGH_ENERGY"
    PV_CENTRE_ENERGY = "CENTRE_ENERGY"

    PV_SLICES = "SLICES"
    PV_DETECTOR_MODE = "DETECTOR_MODE"
    PV_LENS_MODE = "LENS_MODE"
    PV_ENERGY_STEP = "CAM:STEP_SIZE"

    PV_ACQISITION_MODE = "ACQ_MODE"

    PV_PASS_ENERGY = "PASS_ENERGY"
    PV_FIRST_X_CHANNEL = "MinX"
    PV_FIRST_Y_CHANNEL = "MinY"
    PV_LAST_X_CHANNEL = "SizeX"
    PV_LAST_Y_CHANNEL = "SizeY"
    PV_ITERATIONS = "NumExposures"
    PV_IMAGE_MODE = "ImageMode"

    def __init__(self, prefix: str, name: str = "") -> None:
        self.prefix = prefix

        self.region: SESRegion | None = None
        self.excitation_energy: float = 0.0
        self.energy_mode: EnergyMode = EnergyMode.KINETIC

        with self.add_children_as_readables():
            self.low_energy_signal = epics_signal_w(
                float, self.prefix + VGScientaAnalyser.PV_LOW_ENERGY
            )
            self.high_energy_signal = epics_signal_w(
                float, self.prefix + VGScientaAnalyser.PV_HIGH_ENERGY
            )
            self.centre_energy_signal = epics_signal_w(
                float, self.prefix + VGScientaAnalyser.PV_CENTRE_ENERGY
            )

            self.first_x_channel_signal = epics_signal_w(
                int, self.prefix + VGScientaAnalyser.PV_FIRST_X_CHANNEL
            )
            self.first_y_channel_signal = epics_signal_w(
                int, self.prefix + VGScientaAnalyser.PV_FIRST_Y_CHANNEL
            )
            self.last_x_channel_signal = epics_signal_w(
                int, self.prefix + VGScientaAnalyser.PV_LAST_X_CHANNEL
            )
            self.last_y_channel_signal = epics_signal_w(
                int, self.prefix + VGScientaAnalyser.PV_LAST_Y_CHANNEL
            )

            self.slices_signal = epics_signal_w(
                int, self.prefix + VGScientaAnalyser.PV_SLICES
            )
            self.detector_mode_signal = epics_signal_w(
                DetectorMode, self.prefix + VGScientaAnalyser.PV_DETECTOR_MODE
            )
            self.lens_mode_signal = epics_signal_w(
                str, self.prefix + VGScientaAnalyser.PV_LENS_MODE
            )
            self.pass_energy_signal = epics_signal_w(
                int, self.prefix + VGScientaAnalyser.PV_PASS_ENERGY
            )
            self.energy_step_signal = epics_signal_w(
                float, self.prefix + VGScientaAnalyser.PV_ENERGY_STEP
            )

            self.iterations_signal = epics_signal_w(
                int, self.prefix + VGScientaAnalyser.PV_ITERATIONS
            )
            self.image_mode_signal = epics_signal_w(
                str, self.prefix + VGScientaAnalyser.PV_IMAGE_MODE
            )

            self.acquisition_mode_signal = epics_signal_w(
                AcquisitionMode, self.prefix + VGScientaAnalyser.PV_ACQISITION_MODE
            )

        super().__init__(name)
