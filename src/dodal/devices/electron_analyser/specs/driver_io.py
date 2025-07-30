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
from dodal.devices.electron_analyser.abstract.types import TLensMode, TPsuMode
from dodal.devices.electron_analyser.specs.enums import AcquisitionMode
from dodal.devices.electron_analyser.specs.region import SpecsRegion
from dodal.devices.electron_analyser.util import to_kinetic_energy


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
        energy_sources: Mapping[str, SignalR[float]],
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
            energy_sources=energy_sources,
            name=name,
        )

    @AsyncStatus.wrap
    async def set(self, region: SpecsRegion[TLensMode, TPsuMode]):
        source = self._get_energy_source(region.excitation_energy_source)
        excitation_energy = await source.get_value()  # eV

        low_energy = to_kinetic_energy(
            region.low_energy, region.energy_mode, excitation_energy
        )
        centre_energy = to_kinetic_energy(
            region.centre_energy, region.energy_mode, excitation_energy
        )
        high_energy = to_kinetic_energy(
            region.high_energy, region.energy_mode, excitation_energy
        )
        await asyncio.gather(
            self.region_name.set(region.name),
            self.energy_mode.set(region.energy_mode),
            self.low_energy.set(low_energy),
            self.high_energy.set(high_energy),
            self.slices.set(region.slices),
            self.lens_mode.set(region.lens_mode),
            self.pass_energy.set(region.pass_energy),
            self.iterations.set(region.iterations),
            self.acquisition_mode.set(region.acquisition_mode),
            self.excitation_energy.set(excitation_energy),
            self.excitation_energy_source.set(source.name),
            self.snapshot_values.set(region.values),
            self.psu_mode.set(region.psu_mode),
        )
        if region.acquisition_mode == AcquisitionMode.FIXED_TRANSMISSION:
            await self.energy_step.set(region.energy_step)

        if region.acquisition_mode == AcquisitionMode.FIXED_ENERGY:
            await self.centre_energy.set(centre_energy)

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
