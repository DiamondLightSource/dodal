import asyncio
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import numpy as np
from bluesky.protocols import Movable, Preparable
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    SignalR,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_r,
    soft_signal_rw,
)
from ophyd_async.epics.adcore import ADBaseIO
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.devices.electron_analyser.abstract.base_region import (
    TAbstractBaseRegion,
)
from dodal.devices.electron_analyser.enums import EnergyMode
from dodal.devices.electron_analyser.util import to_binding_energy, to_kinetic_energy


class AbstractAnalyserDriverIO(
    ABC,
    StandardReadable,
    ADBaseIO,
    Preparable,
    Movable[TAbstractBaseRegion],
    Generic[TAbstractBaseRegion],
):
    """
    Generic device to configure electron analyser with new region settings.
    Electron analysers should inherit from this class for further specialisation.
    """

    def __init__(
        self, prefix: str, acquisition_mode_type: type[StrictEnum], name: str = ""
    ) -> None:
        with self.add_children_as_readables():
            self.image = epics_signal_r(Array1D[np.float64], prefix + "IMAGE")
            self.spectrum = epics_signal_r(Array1D[np.float64], prefix + "INT_SPECTRUM")
            self.total_intensity = derived_signal_r(
                self._calculate_total_intensity, spectrum=self.spectrum
            )
            self.excitation_energy = soft_signal_rw(float, initial_value=0, units="eV")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Used for setting up region data acquisition.
            self.region_name = soft_signal_rw(str, initial_value="null")
            self.energy_mode = soft_signal_rw(
                EnergyMode, initial_value=EnergyMode.KINETIC
            )
            self.low_energy = epics_signal_rw(float, prefix + "LOW_ENERGY")
            self.high_energy = epics_signal_rw(float, prefix + "HIGH_ENERGY")
            self.slices = epics_signal_rw(int, prefix + "SLICES")
            self.lens_mode = epics_signal_rw(str, prefix + "LENS_MODE")
            self.pass_energy = epics_signal_rw(
                self.pass_energy_type, prefix + "PASS_ENERGY"
            )
            self.energy_step = epics_signal_rw(float, prefix + "STEP_SIZE")
            self.iterations = epics_signal_rw(int, prefix + "NumExposures")
            self.acquisition_mode = epics_signal_rw(
                acquisition_mode_type, prefix + "ACQ_MODE"
            )
            self.excitation_energy_source = soft_signal_rw(str, initial_value="")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Read once per scan after data acquired
            self.energy_axis = self._create_energy_axis_signal(prefix)
            self.binding_energy_axis = derived_signal_r(
                self._calculate_binding_energy_axis,
                "eV",
                energy_axis=self.energy_axis,
                excitation_energy=self.excitation_energy,
                energy_mode=self.energy_mode,
            )
            self.angle_axis = self._create_angle_axis_signal(prefix)
            self.step_time = epics_signal_r(float, prefix + "AcquireTime")
            self.total_steps = epics_signal_r(int, prefix + "TOTAL_POINTS_RBV")
            self.total_time = derived_signal_r(
                self._calculate_total_time,
                "s",
                total_steps=self.total_steps,
                step_time=self.step_time,
                iterations=self.iterations,
            )

        super().__init__(prefix=prefix, name=name)

    @AsyncStatus.wrap
    async def prepare(self, value: Motor):
        """
        Prepare the driver for a region by passing in the energy source motor selected
        by a region.

        Args:
            value: The motor that contains the information on the current excitation
                   energy. Needed to prepare region for epics to accuratly calculate
                   kinetic energy for an energy scan when in binding energy mode.
        """
        energy_source = value
        excitation_energy_value = await energy_source.user_readback.get_value()  # eV
        excitation_energy_source_name = energy_source.name

        await asyncio.gather(
            self.excitation_energy.set(excitation_energy_value),
            self.excitation_energy_source.set(excitation_energy_source_name),
        )

    @AsyncStatus.wrap
    async def set(self, region: TAbstractBaseRegion):
        """
        This should encompass all core region logic which is common to every electron
        analyser for setting up the driver.

        Args:
            region: Contains the parameters to setup the driver for a scan.
        """
        pass_energy_type = self.pass_energy_type
        pass_energy = pass_energy_type(region.pass_energy)

        excitation_energy = await self.excitation_energy.get_value()
        low_energy = to_kinetic_energy(
            region.low_energy, region.energy_mode, excitation_energy
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
            self.pass_energy.set(pass_energy),
            self.iterations.set(region.iterations),
            self.acquisition_mode.set(region.acquisition_mode),
        )

    @abstractmethod
    def _create_angle_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        """
        The signal that defines the angle axis. Depends on analyser model.

        Args:
            prefix: PV string used for connecting to angle axis.

        Returns:
            Signal that can give us angle axis array data.
        """

    @abstractmethod
    def _create_energy_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        """
        The signal that defines the energy axis. Depends on analyser model.

        Args:
            prefix: PV string used for connecting to energy axis.

        Returns:
            Signal that can give us energy axis array data.
        """

    def _calculate_binding_energy_axis(
        self,
        energy_axis: Array1D[np.float64],
        excitation_energy: float,
        energy_mode: EnergyMode,
    ) -> Array1D[np.float64]:
        """
        Calculate the binding energy axis to calibrate the spectra data. Function for a
        derived signal.

        Args:
            energy_axis:       Array data of the original energy_axis from epics.
            excitation_energy: The excitation energy value used for the scan of this
                               region.
            energy_mode:       The energy_mode of the region that was used for the scan
                               of this region.

        Returns:
            Array that is the correct axis for the spectra data.
        """
        is_binding = energy_mode == EnergyMode.BINDING
        return np.array(
            [
                to_binding_energy(i_energy_axis, EnergyMode.KINETIC, excitation_energy)
                if is_binding
                else i_energy_axis
                for i_energy_axis in energy_axis
            ]
        )

    def _calculate_total_time(
        self, total_steps: int, step_time: float, iterations: int
    ) -> float:
        """
        Calulcate the total time the scan takes for this region. Function for a derived
        signal.

        Args:
            total_steps: Number of steps for the region.
            step_time: Time for each step for the region.
            iterations: The number of iterations the region collected data for.

        Returns:
            Calculated total time in seconds.
        """
        return total_steps * step_time * iterations

    def _calculate_total_intensity(self, spectrum: Array1D[np.float64]) -> float:
        return float(np.sum(spectrum, dtype=np.float64))

    @property
    @abstractmethod
    def pass_energy_type(self) -> type:
        """
        Return the type the pass_energy should be. Depends on underlying analyser
        software.

        Returns:
            Type the pass energy parameter from a region needs to be cast to so it can
            be set correctly on the signal.
        """


TAbstractAnalyserDriverIO = TypeVar(
    "TAbstractAnalyserDriverIO", bound=AbstractAnalyserDriverIO
)
