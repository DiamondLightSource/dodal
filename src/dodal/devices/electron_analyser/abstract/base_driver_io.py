from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Generic, TypeVar

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    SignalR,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_r,
    soft_signal_rw,
)
from ophyd_async.epics.adcore import ADBaseIO
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.abstract.base_region import (
    TAbstractBaseRegion,
)
from dodal.devices.electron_analyser.abstract.types import (
    TAcquisitionMode,
    TLensMode,
    TPassEnergy,
    TPsuMode,
)
from dodal.devices.electron_analyser.enums import EnergyMode
from dodal.devices.electron_analyser.util import to_binding_energy


class AbstractAnalyserDriverIO(
    ABC,
    StandardReadable,
    ADBaseIO,
    Movable[TAbstractBaseRegion],
    Generic[TAbstractBaseRegion, TAcquisitionMode, TLensMode, TPsuMode, TPassEnergy],
):
    """
    Driver device that defines signals and readables that should be common to all
    electron analysers. Implementations of electron analyser devices should inherit
    from this class and define additional specialised signals and methods.
    """

    def __init__(
        self,
        prefix: str,
        acquisition_mode_type: type[TAcquisitionMode],
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        pass_energy_type: type[TPassEnergy],
        energy_sources: Mapping[str, SignalR[float]],
        name: str = "",
    ) -> None:
        """
        Constructor method for setting up electron analyser.

        Args:
            prefix: Base PV to connect to EPICS for this device.
            acquisition_mode_type: Enum that determines the available acquisition modes
                                   for this device.
            lens_mode_type: Enum that determines the available lens mode for this
                            device.
            psu_mode_type: Enum that determines the available psu modes for this device.
            pass_energy_type: Can be enum or float, depends on electron analyser model.
                              If enum, it determines the available pass energies for
                              this device.
            energy_sources: Map that pairs a source name to an energy value signal
                            (in eV).
            name: Name of the device.
        """
        self.energy_sources = energy_sources
        self.acquisition_mode_type = acquisition_mode_type
        self.lens_mode_type = lens_mode_type
        self.psu_mode_type = psu_mode_type
        self.pass_energy_type = pass_energy_type

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
            self.centre_energy = epics_signal_rw(float, prefix + "CENTRE_ENERGY")
            self.high_energy = epics_signal_rw(float, prefix + "HIGH_ENERGY")
            self.slices = epics_signal_rw(int, prefix + "SLICES")
            self.lens_mode = epics_signal_rw(lens_mode_type, prefix + "LENS_MODE")
            self.pass_energy = epics_signal_rw(pass_energy_type, prefix + "PASS_ENERGY")
            self.energy_step = epics_signal_rw(float, prefix + "STEP_SIZE")
            self.iterations = epics_signal_rw(int, prefix + "NumExposures")
            self.acquisition_mode = epics_signal_rw(
                acquisition_mode_type, prefix + "ACQ_MODE"
            )
            self.excitation_energy_source = soft_signal_rw(str, initial_value="")
            # This is used by each electron analyser, however it depends on the electron
            # analyser type to know if is moved with region settings.
            self.psu_mode = epics_signal_rw(psu_mode_type, prefix + "PSU_MODE")

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

    @abstractmethod
    @AsyncStatus.wrap
    async def set(self, region: TAbstractBaseRegion):
        """
        Move a group of signals defined in a region. Each implementation of this class
        is responsible for implementing this method correctly.

        Args:
            region: Contains the parameters to setup the driver for a scan.
        """

    def _get_energy_source(self, alias_name: str) -> SignalR[float]:
        energy_source = self.energy_sources.get(alias_name)
        if energy_source is None:
            raise KeyError(
                f"'{energy_source}' is an invalid energy source. Avaliable energy "
                + f"sources are '{list(self.energy_sources.keys())}'"
            )
        return energy_source

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


TAbstractAnalyserDriverIO = TypeVar(
    "TAbstractAnalyserDriverIO", bound=AbstractAnalyserDriverIO
)
