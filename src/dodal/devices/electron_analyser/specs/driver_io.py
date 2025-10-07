import asyncio
from typing import Generic

import numpy as np
from ophyd_async.core import (
    Array1D,
    SignalR,
    StandardReadableFormat,
    derived_signal_r,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.abstract.base_driver_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract.types import TLensMode, TPsuMode
from dodal.devices.electron_analyser.energy_sources import (
    DualEnergySource,
    EnergySource,
)
from dodal.devices.electron_analyser.specs.enums import AcquisitionMode
from dodal.devices.electron_analyser.specs.region import SpecsRegion


class SpecsAnalyserDriverIO(
    AbstractAnalyserDriverIO[
        SpecsRegion[TLensMode, TPsuMode],
        AcquisitionMode,
        TLensMode,
        TPsuMode,
        float,
    ],
    Generic[TLensMode, TPsuMode],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        energy_source: EnergySource | DualEnergySource,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Used for setting up region data acquisition.
            self.snapshot_values = epics_signal_rw(int, prefix + "VALUES")

        # Used to calculate the angle axis.
        self.min_angle_axis = epics_signal_r(float, prefix + "Y_MIN_RBV")
        self.max_angle_axis = epics_signal_r(float, prefix + "Y_MAX_RBV")

        # Used to calculate the energy axis.
        self.energy_channels = epics_signal_r(
            int, prefix + "TOTAL_POINTS_ITERATION_RBV"
        )

        super().__init__(
            prefix=prefix,
            acquisition_mode_type=AcquisitionMode,
            lens_mode_type=lens_mode_type,
            psu_mode_type=psu_mode_type,
            pass_energy_type=float,
            energy_source=energy_source,
            name=name,
        )

    async def _set_region(self, ke_region: SpecsRegion[TLensMode, TPsuMode]):
        await asyncio.gather(
            self.region_name.set(ke_region.name),
            self.low_energy.set(ke_region.low_energy),
            self.high_energy.set(ke_region.high_energy),
            self.slices.set(ke_region.slices),
            self.acquire_time.set(ke_region.acquire_time),
            self.lens_mode.set(ke_region.lens_mode),
            self.pass_energy.set(ke_region.pass_energy),
            self.iterations.set(ke_region.iterations),
            self.acquisition_mode.set(ke_region.acquisition_mode),
            self.snapshot_values.set(ke_region.values),
            self.psu_mode.set(ke_region.psu_mode),
        )
        if ke_region.acquisition_mode == AcquisitionMode.FIXED_TRANSMISSION:
            await self.energy_step.set(ke_region.energy_step)

        if ke_region.acquisition_mode == AcquisitionMode.FIXED_ENERGY:
            await self.centre_energy.set(ke_region.centre_energy)

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
            total_points_iterations=self.energy_channels,
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
