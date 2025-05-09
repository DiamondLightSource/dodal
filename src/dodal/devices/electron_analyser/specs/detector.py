import asyncio

from dodal.devices.electron_analyser.abstract.base_detector import (
    AbstractElectronAnalyserDetector,
    AbstractElectronAnalyserRegionDetector,
)
from dodal.devices.electron_analyser.specs.driver_io import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.specs.region import SpecsRegion, SpecsSequence


class SpecsRegionDetector(
    AbstractElectronAnalyserRegionDetector[SpecsAnalyserDriverIO, SpecsRegion]
):
    async def configure_specific_region(self, excitation_energy) -> None:
        await asyncio.gather(
            self.driver.snapshot_values.set(self.region.values),
            self.driver.psu_mode.set(self.region.psu_mode),
        )
        if self.region.acquisition_mode == "Fixed Transmission":
            self.driver.centre_energy.set(self.region.centre_energy)

        if self.region.acquisition_mode == "Fixed Energy":
            self.driver.energy_step.set(self.region.energy_step)


class SpecsDetector(
    AbstractElectronAnalyserDetector[
        SpecsRegionDetector, SpecsAnalyserDriverIO, SpecsSequence, SpecsRegion
    ]
):
    def __init__(self, prefix: str, name: str):
        super().__init__(prefix, name, SpecsSequence)

    def _create_driver(self, prefix: str) -> SpecsAnalyserDriverIO:
        return SpecsAnalyserDriverIO(prefix, "driver")

    def _create_region_detector(
        self, driver: SpecsAnalyserDriverIO, region: SpecsRegion
    ) -> SpecsRegionDetector:
        return SpecsRegionDetector(self.name, driver, region)
