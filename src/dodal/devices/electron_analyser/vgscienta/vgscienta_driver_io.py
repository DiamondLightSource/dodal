import asyncio
from typing import Generic

import numpy as np
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    SignalR,
    StandardReadableFormat,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.base.base_driver_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.base.base_region import TLensMode, TPsuMode
from dodal.devices.electron_analyser.vgscienta.vgscienta_enums import (
    AcquisitionMode,
    DetectorMode,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_region import (
    TPassEnergyEnum,
    VGScientaRegion,
)


class VGScientaAnalyserDriverIO(
    AbstractAnalyserDriverIO[
        VGScientaRegion[TLensMode, TPassEnergyEnum],
        AcquisitionMode,
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
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Used for setting up region data acquisition.
            self.detector_mode = epics_signal_rw(DetectorMode, prefix + "DETECTOR_MODE")

            self.region_min_x = epics_signal_rw(int, prefix + "MinX")
            self.region_size_x = epics_signal_rw(int, prefix + "SizeX")
            self.sensor_max_size_x = epics_signal_r(int, prefix + "MaxSizeX_RBV")

            self.region_min_y = epics_signal_rw(int, prefix + "MinY")
            self.region_size_y = epics_signal_rw(int, prefix + "SizeY")
            self.sensor_max_size_y = epics_signal_r(int, prefix + "MaxSizeY_RBV")

        super().__init__(
            prefix,
            AcquisitionMode,
            lens_mode_type,
            psu_mode_type,
            pass_energy_type,
            name,
        )

    @AsyncStatus.wrap
    async def set(self, epics_region: VGScientaRegion[TLensMode, TPassEnergyEnum]):
        await asyncio.gather(
            self.region_name.set(epics_region.name),
            self.low_energy.set(epics_region.low_energy),
            self.centre_energy.set(epics_region.centre_energy),
            self.high_energy.set(epics_region.high_energy),
            self.slices.set(epics_region.slices),
            self.lens_mode.set(epics_region.lens_mode),
            self.pass_energy.set(epics_region.pass_energy),
            self.iterations.set(epics_region.iterations),
            self.acquire_time.set(epics_region.acquire_time),
            self.acquisition_mode.set(epics_region.acquisition_mode),
            self.energy_step.set(epics_region.energy_step),
            self.detector_mode.set(epics_region.detector_mode),
            self.region_min_x.set(epics_region.min_x),
            self.region_size_x.set(epics_region.size_x),
            self.region_min_y.set(epics_region.min_y),
            self.region_size_y.set(epics_region.size_y),
            self.energy_mode.set(epics_region.energy_mode),
        )

    def _create_energy_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        return epics_signal_r(Array1D[np.float64], prefix + "X_SCALE_RBV")

    def _create_angle_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        return epics_signal_r(Array1D[np.float64], prefix + "Y_SCALE_RBV")
