import asyncio

from ophyd_async.core import AsyncStatus
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.abstract_analyser_controller import (
    AbstractAnalyserController,
)
from dodal.devices.electron_analyser.vgscienta_region import (
    DetectorMode,
    VGScientaRegion,
)


class VGScientaAnalyserController(AbstractAnalyserController):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.centre_energy = epics_signal_rw(float, prefix + "CENTRE_ENERGY")
            self.first_x_channel = epics_signal_rw(int, prefix + "MinX")
            self.first_y_channel = epics_signal_rw(int, prefix + "MinY")
            self.x_channel_size = epics_signal_rw(int, prefix + "SizeX")
            self.y_channel_size = epics_signal_rw(int, prefix + "SizeY")
            self.detector_mode = epics_signal_rw(DetectorMode, prefix + "DETECTOR_MODE")
            self.energy_step = epics_signal_rw(float, prefix + "STEP_SIZE")
            self.image_mode = epics_signal_rw(str, prefix + "ImageMode")

        super().__init__(prefix, name)

    @AsyncStatus.wrap
    async def set(
        self, region: VGScientaRegion, excitation_energy_eV: float, *args, **kwargs
    ):
        centre_energy = region.to_kinetic_energy(
            region.fix_energy, excitation_energy_eV
        )
        energy_step_eV = region.get_energy_step_eV()

        await asyncio.gather(
            super().set(region, excitation_energy_eV),
            self.centre_energy.set(centre_energy),
            self.energy_step.set(energy_step_eV),
            self.first_x_channel.set(region.first_x_channel),
            self.first_y_channel.set(region.first_y_channel),
            self.x_channel_size.set(region.x_channel_size()),
            self.y_channel_size.set(region.y_channel_size()),
            self.detector_mode.set(region.detector_mode),
            self.image_mode.set("Single"),
        )
