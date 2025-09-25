from typing import Generic

from dodal.devices.electron_analyser.abstract.types import (
    TLensMode,
    TPassEnergyEnum,
    TPsuMode,
)
from dodal.devices.electron_analyser.detector import (
    ElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.energy_sources import (
    DualEnergySource,
    EnergySource,
)
from dodal.devices.electron_analyser.vgscienta.driver_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta.region import (
    VGScientaRegion,
    VGScientaSequence,
)


class VGScientaDetector(
    ElectronAnalyserDetector[
        VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum],
        VGScientaSequence[TLensMode, TPsuMode, TPassEnergyEnum],
        VGScientaRegion[TLensMode, TPassEnergyEnum],
    ],
    Generic[TLensMode, TPsuMode, TPassEnergyEnum],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        pass_energy_type: type[TPassEnergyEnum],
        energy_source: DualEnergySource | EnergySource,
        name: str = "",
    ):
        driver = VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum](
            prefix, lens_mode_type, psu_mode_type, pass_energy_type, energy_source
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
            driver.detector_mode,
            driver.region_min_x,
            driver.region_size_x,
            driver.sensor_max_size_x,
            driver.region_min_y,
            driver.region_size_y,
            driver.sensor_max_size_y,
        )
        super().__init__(
            VGScientaSequence[lens_mode_type, psu_mode_type, pass_energy_type],
            driver,
            config_sigs,
            name,
        )
