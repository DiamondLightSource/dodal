import asyncio
from collections.abc import Mapping
from typing import Generic

import numpy as np
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    SignalR,
    StandardReadableFormat,
)
from ophyd_async.epics.adcore import ADImageMode
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.abstract.base_driver_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract.types import (
    TLensMode,
    TPassEnergyEnum,
    TPsuMode,
)
from dodal.devices.electron_analyser.util import to_kinetic_energy
from dodal.devices.electron_analyser.vgscienta.enums import (
    AcquisitionMode,
    DetectorMode,
)
from dodal.devices.electron_analyser.vgscienta.region import VGScientaRegion


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
        energy_sources: Mapping[str, SignalR[float]],
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Used for setting up region data acquisition.
            self.centre_energy = epics_signal_rw(float, prefix + "CENTRE_ENERGY")
            self.first_x_channel = epics_signal_rw(int, prefix + "MinX")
            self.first_y_channel = epics_signal_rw(int, prefix + "MinY")
            self.x_channel_size = epics_signal_rw(int, prefix + "SizeX")
            self.y_channel_size = epics_signal_rw(int, prefix + "SizeY")
            self.detector_mode = epics_signal_rw(DetectorMode, prefix + "DETECTOR_MODE")

        super().__init__(
            prefix,
            AcquisitionMode,
            lens_mode_type,
            psu_mode_type,
            pass_energy_type,
            energy_sources,
            name,
        )

    @AsyncStatus.wrap
    async def set(self, region: VGScientaRegion[TLensMode, TPassEnergyEnum]):
        await super().set(region)

        excitation_energy = await self.excitation_energy.get_value()
        centre_energy = to_kinetic_energy(
            region.fix_energy, region.energy_mode, excitation_energy
        )
        await asyncio.gather(
            self.centre_energy.set(centre_energy),
            self.energy_step.set(region.energy_step),
            self.first_x_channel.set(region.first_x_channel),
            self.first_y_channel.set(region.first_y_channel),
            self.x_channel_size.set(region.x_channel_size()),
            self.y_channel_size.set(region.y_channel_size()),
            self.detector_mode.set(region.detector_mode),
            self.image_mode.set(ADImageMode.SINGLE),
        )

    def _create_energy_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        return epics_signal_r(Array1D[np.float64], prefix + "X_SCALE_RBV")

    def _create_angle_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        return epics_signal_r(Array1D[np.float64], prefix + "Y_SCALE_RBV")
