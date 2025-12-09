import asyncio
from typing import Generic

import numpy as np
from ophyd_async.core import (
    Array1D,
    SignalR,
    StandardReadableFormat,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.driver_io.base_driver_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.energy_sources import (
    DualEnergySource,
    EnergySource,
)
from dodal.devices.electron_analyser.enums import (
    VGScientaAcquisitionMode,
    VGScientaDetectorMode,
)
from dodal.devices.electron_analyser.region.vgscienta_region import (
    VGScientaRegion,
)
from dodal.devices.electron_analyser.types.base_types import (
    TLensMode,
    TPassEnergyEnum,
    TPsuMode,
)


class VGScientaAnalyserDriverIO(
    AbstractAnalyserDriverIO[
        VGScientaRegion[TLensMode, TPassEnergyEnum],
        VGScientaAcquisitionMode,
        TLensMode,
        TPsuMode,
        TPassEnergyEnum,
    ],
    Generic[TLensMode, TPsuMode, TPassEnergyEnum],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        pass_energy_type: type[TPassEnergyEnum],
        energy_source: EnergySource | DualEnergySource,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Used for setting up region data acquisition.
            self.detector_mode = epics_signal_rw(
                VGScientaDetectorMode, prefix + "DETECTOR_MODE"
            )

            self.region_min_x = epics_signal_rw(int, prefix + "MinX")
            self.region_size_x = epics_signal_rw(int, prefix + "SizeX")
            self.sensor_max_size_x = epics_signal_r(int, prefix + "MaxSizeX_RBV")

            self.region_min_y = epics_signal_rw(int, prefix + "MinY")
            self.region_size_y = epics_signal_rw(int, prefix + "SizeY")
            self.sensor_max_size_y = epics_signal_r(int, prefix + "MaxSizeY_RBV")

        super().__init__(
            prefix,
            VGScientaAcquisitionMode,
            lens_mode_type,
            psu_mode_type,
            pass_energy_type,
            energy_source,
            name,
        )

    async def _set_region(self, ke_region: VGScientaRegion[TLensMode, TPassEnergyEnum]):
        await asyncio.gather(
            self.region_name.set(ke_region.name),
            self.low_energy.set(ke_region.low_energy),
            self.centre_energy.set(ke_region.centre_energy),
            self.high_energy.set(ke_region.high_energy),
            self.slices.set(ke_region.slices),
            self.lens_mode.set(ke_region.lens_mode),
            self.pass_energy.set(ke_region.pass_energy),
            self.iterations.set(ke_region.iterations),
            self.acquire_time.set(ke_region.acquire_time),
            self.acquisition_mode.set(ke_region.acquisition_mode),
            self.energy_step.set(ke_region.energy_step),
            self.detector_mode.set(ke_region.detector_mode),
            self.region_min_x.set(ke_region.min_x),
            self.region_size_x.set(ke_region.size_x),
            self.region_min_y.set(ke_region.min_y),
            self.region_size_y.set(ke_region.size_y),
        )

    def _create_energy_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        return epics_signal_r(Array1D[np.float64], prefix + "X_SCALE_RBV")

    def _create_angle_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        return epics_signal_r(Array1D[np.float64], prefix + "Y_SCALE_RBV")
