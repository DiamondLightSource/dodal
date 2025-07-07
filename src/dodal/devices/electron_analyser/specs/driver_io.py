import asyncio
from collections.abc import Mapping
from typing import Generic

import numpy as np
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    SignalR,
    StandardReadableFormat,
    derived_signal_r,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.abstract.base_driver_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract.base_region import TLensMode
from dodal.devices.electron_analyser.specs.enums import AcquisitionMode, PsuMode
from dodal.devices.electron_analyser.specs.region import SpecsRegion


class SpecsAnalyserDriverIO(
    AbstractAnalyserDriverIO[SpecsRegion, AcquisitionMode, TLensMode],
    Generic[TLensMode],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        energy_sources: Mapping[str, SignalR[float]],
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Used for setting up region data acquisition.
            self.psu_mode = epics_signal_rw(PsuMode, prefix + "SCAN_RANGE")
            self.snapshot_values = epics_signal_rw(int, prefix + "VALUES")
            self.centre_energy = epics_signal_rw(float, prefix + "KINETIC_ENERGY")

            # Used to read detector data after acqusition.
            self.min_angle_axis = epics_signal_r(float, prefix + "Y_MIN_RBV")
            self.max_angle_axis = epics_signal_r(float, prefix + "Y_MAX_RBV")

        super().__init__(prefix, AcquisitionMode, lens_mode_type, energy_sources, name)

    @AsyncStatus.wrap
    async def set(self, region: SpecsRegion[TLensMode]):
        await super().set(region)

        await asyncio.gather(
            self.snapshot_values.set(region.values),
            self.psu_mode.set(region.psu_mode),
        )
        if region.acquisition_mode == AcquisitionMode.FIXED_TRANSMISSION:
            await self.centre_energy.set(region.centre_energy)

        if self.acquisition_mode == AcquisitionMode.FIXED_ENERGY:
            await self.energy_step.set(region.energy_step)

    def _create_angle_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        angle_axis = derived_signal_r(
            self._calculate_angle_axis,
            min_angle=self.min_angle_axis,
            max_angle=self.max_angle_axis,
            slices=self.slices,
        )
        return angle_axis

    def _calculate_angle_axis(
        self, min_angle: float, max_angle: float, slices: int
    ) -> Array1D[np.float64]:
        # SPECS returns the extreme edges of the range, not the centre of the pixels
        width = (max_angle - min_angle) / slices
        offset = width / 2

        axis = np.array([min_angle + offset + i * width for i in range(slices)])
        return axis

    def _create_energy_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        energy_axis = derived_signal_r(
            self._calculate_energy_axis,
            "eV",
            min_energy=self.low_energy,
            max_energy=self.high_energy,
            total_points_iterations=self.slices,
        )
        return energy_axis

    def _calculate_energy_axis(
        self, min_energy: float, max_energy: float, total_points_iterations: int
    ) -> Array1D[np.float64]:
        # Note: Don't use the energy step because of the case where the step doesn't
        # exactly fill the range
        step = (max_energy - min_energy) / (total_points_iterations - 1)
        axis = np.array([min_energy + i * step for i in range(total_points_iterations)])
        return axis

    @property
    def pass_energy_type(self) -> type:
        return float
