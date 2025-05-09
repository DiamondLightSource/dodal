from abc import ABC, abstractmethod
from typing import TypeVar

import numpy as np
from ophyd_async.core import (
    Array1D,
    SignalR,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_r,
    soft_signal_rw,
)
from ophyd_async.epics.adcore import ADBaseIO
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.types import EnergyMode
from dodal.devices.electron_analyser.util import to_binding_energy


class AbstractAnalyserDriverIO(ABC, StandardReadable, ADBaseIO):
    """
    Generic device to configure electron analyser with new region settings.
    Electron analysers should inherit from this class for further specialisation.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
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
            self.acquisition_mode = epics_signal_rw(str, prefix + "ACQ_MODE")

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
    def _create_angle_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        """
        The signal that defines the angle axis. Depends on analyser model.
        """

    @abstractmethod
    def _create_energy_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        """
        The signal that defines the energy axis. Depends on analyser model.
        """

    def _calculate_binding_energy_axis(
        self,
        energy_axis: Array1D[np.float64],
        excitation_energy: float,
        energy_mode: EnergyMode,
    ) -> Array1D[np.float64]:
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
        return total_steps * step_time * iterations

    def _calculate_total_intensity(self, spectrum: Array1D[np.float64]) -> float:
        return float(np.sum(spectrum, dtype=np.float64))

    @property
    @abstractmethod
    def pass_energy_type(self) -> type:
        """
        Return the type the pass_energy should be. Each one is unfortunately different
        for the underlying analyser software and cannot be changed on epics side.
        """


TAbstractAnalyserDriverIO = TypeVar(
    "TAbstractAnalyserDriverIO", bound=AbstractAnalyserDriverIO
)
