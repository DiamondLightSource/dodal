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
from dodal.devices.electron_analyser.enums import EnergyMode, SelectedSource
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
    """
    SpecsAnalyserDriverIO is a driver interface for controlling and configuring a SPECS electron analyser device.
    It manages the setup and acquisition of region data, including energy and angle axes, lens and PSU modes,
    and acquisition parameters.

    Type Parameters:
        TLensMode: Type for lens mode enumeration.
        TPsuMode: Type for PSU mode enumeration.

    Args:
        prefix (str): The EPICS PV prefix for the analyser device.
        lens_mode_type (type[TLensMode]): The type of lens mode supported by the analyser.
        psu_mode_type (type[TPsuMode]): The type of PSU mode supported by the analyser.
        energy_sources (Mapping[SelectedSource, SignalR[float]]): Mapping of selectable energy sources to their signals.
        name (str, optional): Name of the device instance.

    Attributes:
        snapshot_values: Signal for setting up region data acquisition.
        min_angle_axis: Signal for the minimum value of the angle axis.
        max_angle_axis: Signal for the maximum value of the angle axis.
        energy_channels: Signal for the number of energy channels (points per iteration).

    Methods:
        set(region): Asynchronously configures the analyser for a given region, setting all relevant parameters.
        _create_angle_axis_signal(prefix): Creates a derived signal representing the angle axis.
        _calculate_angle_axis(min_angle, max_angle, slices): Calculates the angle axis array based on region parameters.
        _create_energy_axis_signal(prefix): Creates a derived signal representing the energy axis.
        _calculate_energy_axis(min_energy, max_energy, total_points_iterations): Calculates the energy axis array.

    Notes:
        - The class ensures that region configuration is always converted to kinetic energy mode before applying.
        - Axis calculations account for device-specific conventions (e.g., edge vs. center pixel definitions).
    """

    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        energy_sources: Mapping[SelectedSource, SignalR[float]],
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
        # Copy region so doesn't alter the actual region and switch to kinetic energy
        ke_region = region.model_copy()
        ke_region.switch_energy_mode(EnergyMode.KINETIC, excitation_energy)

        await asyncio.gather(
            self.region_name.set(ke_region.name),
            self.energy_mode.set(ke_region.energy_mode),
            self.low_energy.set(ke_region.low_energy),
            self.high_energy.set(ke_region.high_energy),
            self.slices.set(ke_region.slices),
            self.acquire_time.set(ke_region.acquire_time),
            self.lens_mode.set(ke_region.lens_mode),
            self.pass_energy.set(ke_region.pass_energy),
            self.iterations.set(ke_region.iterations),
            self.acquisition_mode.set(ke_region.acquisition_mode),
            self.excitation_energy.set(excitation_energy),
            self.excitation_energy_source.set(source.name),
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
