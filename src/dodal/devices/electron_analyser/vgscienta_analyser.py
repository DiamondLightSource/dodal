import asyncio

from ophyd_async.core import AsyncStatus
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.base_analyser import BaseAnalyser
from dodal.devices.electron_analyser.vgscienta_region import (
    DetectorMode,
    VGScientaRegion,
)


class VGScientaAnalyser(BaseAnalyser):
    PV_CENTRE_ENERGY = "CENTRE_ENERGY"
    PV_DETECTOR_MODE = "DETECTOR_MODE"
    PV_ENERGY_STEP = "STEP_SIZE"
    PV_FIRST_X_CHANNEL = "MinX"
    PV_FIRST_Y_CHANNEL = "MinY"
    PV_X_CHANNEL_SIZE = "SizeX"
    PV_Y_CHANNEL_SIZE = "SizeY"
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
            self.x_channel_size_signal = epics_signal_rw(
                int, self.prefix + VGScientaAnalyser.PV_X_CHANNEL_SIZE
            )
            self.y_channel_size_signal = epics_signal_rw(
                int, self.prefix + VGScientaAnalyser.PV_Y_CHANNEL_SIZE
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

    def get_pass_energy_type(self) -> type:
        return str

    @AsyncStatus.wrap
    async def set(
        self, value: VGScientaRegion, excitation_energy_eV: float, *args, **kwargs
    ):
        region = value
        centre_energy = region.to_kinetic_energy(region.fixEnergy, excitation_energy_eV)
        energy_step_eV = region.get_energy_step_eV()

        await asyncio.gather(
            super().set(region, excitation_energy_eV),
            self.centre_energy_signal.set(centre_energy),
            self.energy_step_signal.set(energy_step_eV),
            self.first_x_channel_signal.set(region.firstXChannel),
            self.first_y_channel_signal.set(region.firstYChannel),
            self.x_channel_size_signal.set(region.x_channel_size()),
            self.y_channel_size_signal.set(region.y_channel_size()),
            self.detector_mode_signal.set(region.detectorMode),
            self.image_mode_signal.set("Single"),
        )
