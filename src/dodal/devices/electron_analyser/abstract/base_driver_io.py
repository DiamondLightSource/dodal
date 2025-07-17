import asyncio
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Annotated as A
from typing import Generic, TypeVar

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    SignalR,
    SignalRW,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_r,
    soft_signal_rw,
)
from ophyd_async.epics.adcore import ADBaseIO
from ophyd_async.epics.core import (
    PvSuffix,
    epics_signal_rw,
)

from dodal.devices.electron_analyser.abstract.base_region import (
    TAbstractBaseRegion,
    TAcquisitionMode,
    TLensMode,
)
from dodal.devices.electron_analyser.enums import EnergyMode
from dodal.devices.electron_analyser.util import to_binding_energy, to_kinetic_energy


class AnalyserDriverBaseIO:
    """
    Base class with PVs common for all electron analyser drivers.
    """

    image: A[SignalR[Array1D[np.double]], PvSuffix("IMAGE")]
    spectrum: A[SignalR[Array1D[np.float64]], PvSuffix("INT_SPECTRUM")]
    total_steps: A[SignalR[int], PvSuffix("TOTAL_POINTS_RBV")]
    low_energy: A[SignalRW[float], PvSuffix.rbv("LOW_ENERGY")]
    high_energy: A[SignalRW[float], PvSuffix.rbv("HIGH_ENERGY")]
    energy_step: A[SignalRW[float], PvSuffix.rbv("STEP_SIZE")]
    slices: A[SignalRW[int], PvSuffix.rbv("SLICES")]


class AbstractAnalyserDriverIO(
    ABC,
    StandardReadable,
    ADBaseIO,
    AnalyserDriverBaseIO,
    Movable[TAbstractBaseRegion],
    Generic[TAbstractBaseRegion, TAcquisitionMode, TLensMode],
):
    """
    Generic device to configure electron analyser with new region settings.
    Electron analysers should inherit from this class for further specialisation.
    """

    def __init__(
        self,
        prefix: str,
        acquisition_mode_type: type[TAcquisitionMode],
        lens_mode_type: type[TLensMode],
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
            energy_sources: Map that pairs a source name to an energy value signal
                            (in eV).
            name: Name of the device.
        """
        self.energy_sources = energy_sources
        self.acquisition_mode_type = acquisition_mode_type
        self.lens_mode_type = lens_mode_type

        # called first to initiate all pydantic parents classes
        super().__init__(prefix=prefix, name=name)

        # add all necessary analyser signals
        self.iterations = epics_signal_rw(int, prefix + "NumExposures")
        self.lens_mode = epics_signal_rw(lens_mode_type, prefix + "LENS_MODE")
        self.pass_energy = epics_signal_rw(
            self.pass_energy_type, prefix + "PASS_ENERGY"
        )

        self.acquisition_mode = epics_signal_rw(
            acquisition_mode_type, prefix + "ACQ_MODE"
        )
        self.region_name = soft_signal_rw(str, initial_value="null")
        self.energy_mode = soft_signal_rw(EnergyMode, initial_value=EnergyMode.KINETIC)
        self.excitation_energy_source = soft_signal_rw(str, initial_value="")
        self.excitation_energy = soft_signal_rw(float, initial_value=0, units="eV")
        self.energy_axis = self._create_energy_axis_signal(prefix)
        self.angle_axis = self._create_angle_axis_signal(prefix)
        self.binding_energy_axis = derived_signal_r(
            self._calculate_binding_energy_axis,
            "eV",
            energy_axis=self.energy_axis,
            excitation_energy=self.excitation_energy,
            energy_mode=self.energy_mode,
        )
        self.total_intensity = derived_signal_r(
            self._calculate_total_intensity, spectrum=self.spectrum
        )
        self.total_time = derived_signal_r(
            self._calculate_total_time,
            "s",
            total_steps=self.total_steps,
            step_time=self.acquire_time,
            iterations=self.iterations,
        )

        # configure per point signals
        self.add_readables(
            [self.image, self.spectrum, self.total_intensity, self.excitation_energy]
        )

        # configure per scan signals
        self.add_readables(
            [
                self.low_energy,
                self.high_energy,
                self.energy_step,
                self.slices,
                self.image_mode,
                self.region_name,
                self.energy_mode,
                self.lens_mode,
                self.pass_energy,
                self.iterations,
                self.acquisition_mode,
                self.excitation_energy_source,
                self.energy_axis,
                self.binding_energy_axis,
                self.angle_axis,
                self.acquire_time,
                self.total_steps,
                self.total_time,
            ],
            StandardReadableFormat.CONFIG_SIGNAL,
        )

    @AsyncStatus.wrap
    async def set(self, region: TAbstractBaseRegion):
        """
        This should encompass all core region logic which is common to every electron
        analyser for setting up the driver.

        Args:
            region: Contains the parameters to setup the driver for a scan.
        """

        source = self._get_energy_source(region.excitation_energy_source)
        excitation_energy = await source.get_value()  # eV

        pass_energy_type = self.pass_energy_type
        pass_energy = pass_energy_type(region.pass_energy)

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
            self.excitation_energy.set(excitation_energy),
            self.excitation_energy_source.set(source.name),
            self.acquire_time.set(region.acquire_time),
        )

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
