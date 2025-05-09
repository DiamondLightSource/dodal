import asyncio

from ophyd_async.epics.adcore import ADImageMode

from dodal.devices.electron_analyser.abstract.base_detector import (
    AbstractElectronAnalyserDetector,
    AbstractElectronAnalyserRegionDetector,
)
from dodal.devices.electron_analyser.util import to_kinetic_energy
from dodal.devices.electron_analyser.vgscienta.driver_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta.region import (
    VGScientaRegion,
    VGScientaSequence,
)


class VGScientaRegionDetector(
    AbstractElectronAnalyserRegionDetector[VGScientaAnalyserDriverIO, VGScientaRegion]
):
    async def configure_specific_region(self, excitation_energy) -> None:
        centre_energy = to_kinetic_energy(
            self.region.fix_energy, self.region.energy_mode, excitation_energy
        )
        await asyncio.gather(
            self.driver.centre_energy.set(centre_energy),
            self.driver.energy_step.set(self.region.energy_step),
            self.driver.first_x_channel.set(self.region.first_x_channel),
            self.driver.first_y_channel.set(self.region.first_y_channel),
            self.driver.x_channel_size.set(self.region.x_channel_size()),
            self.driver.y_channel_size.set(self.region.y_channel_size()),
            self.driver.detector_mode.set(self.region.detector_mode),
            self.driver.excitation_energy_source.set(
                self.region.excitation_energy_source
            ),
            self.driver.image_mode.set(ADImageMode.SINGLE),
        )


class VGScientaDetector(
    AbstractElectronAnalyserDetector[
        VGScientaRegionDetector,
        VGScientaAnalyserDriverIO,
        VGScientaSequence,
        VGScientaRegion,
    ]
):
    def __init__(self, prefix: str, name: str):
        super().__init__(prefix, name, VGScientaSequence)

    def _create_driver(self, prefix: str) -> VGScientaAnalyserDriverIO:
        return VGScientaAnalyserDriverIO(prefix, "driver")

    def _create_region_detector(
        self, driver: VGScientaAnalyserDriverIO, region: VGScientaRegion
    ) -> VGScientaRegionDetector:
        return VGScientaRegionDetector(self.name, driver, region)
