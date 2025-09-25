from typing import Generic

from dodal.devices.electron_analyser.abstract.types import TLensMode, TPsuMode
from dodal.devices.electron_analyser.detector import (
    ElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.energy_sources import (
    DualEnergySource,
    EnergySource,
)
from dodal.devices.electron_analyser.specs.driver_io import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.specs.region import SpecsRegion, SpecsSequence


class SpecsDetector(
    ElectronAnalyserDetector[
        SpecsAnalyserDriverIO[TLensMode, TPsuMode],
        SpecsSequence[TLensMode, TPsuMode],
        SpecsRegion[TLensMode, TPsuMode],
    ],
    Generic[TLensMode, TPsuMode],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        energy_source: DualEnergySource | EnergySource,
        name: str = "",
    ):
        driver = SpecsAnalyserDriverIO[TLensMode, TPsuMode](
            prefix, lens_mode_type, psu_mode_type, energy_source
        )

        if isinstance(energy_source, DualEnergySource):
            energy_config_signals = (
                energy_source.source1.wrapped_device_name,
                energy_source.source2.wrapped_device_name,
            )
        else:
            energy_config_signals = (energy_source.wrapped_device_name,)

        config_sigs = (
            driver.region_name,
            driver.energy_mode,
            driver.low_energy,
            driver.centre_energy,
            driver.high_energy,
            driver.slices,
            driver.lens_mode,
            driver.pass_energy,
            driver.energy_step,
            driver.iterations,
            driver.acquisition_mode,
            driver.psu_mode,
            driver.acquire_time,
            driver.total_steps,
            driver.total_time,
            driver.energy_axis,
            driver.binding_energy_axis,
            driver.angle_axis,
            *energy_config_signals,
            # Specifc to this analyser
            driver.snapshot_values,
        )
        super().__init__(
            SpecsSequence[lens_mode_type, psu_mode_type], driver, config_sigs, name
        )
