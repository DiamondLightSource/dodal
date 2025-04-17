from abc import ABC, abstractmethod
from typing import TypeVar

import numpy as np
from ophyd_async.core import (
    Array1D,
    SignalR,
    StandardReadable,
    soft_signal_rw,
)
from ophyd_async.epics.adcore import ADBaseIO
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.signal_utils import create_r_hardware_backed_soft_signal
from dodal.devices.electron_analyser.abstract_region import EnergyMode
from dodal.devices.electron_analyser.util import to_binding_energy


class AbstractAnalyserDriverIO(ABC, StandardReadable, ADBaseIO):
    """
    Generic device to configure electron analyser with new region settings.
    Electron analysers should inherit from this class for further specialisation.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            # Used for setting up region data acquisition. Read per scan
            self.region_name = soft_signal_rw(str, initial_value="null")
            self.excitation_energy = soft_signal_rw(float, initial_value=0, units="eV")
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

            # Read per scan
            self.energy_axis = self._get_energy_axis_signal(prefix)
            self.binding_energy_axis = create_r_hardware_backed_soft_signal(
                Array1D[np.float64], self._calculate_binding_energy_axis
            )
            self.angle_axis = self._get_angle_axis_signal(prefix)
            self.step_time = epics_signal_r(float, prefix + "AcquireTime")
            self.total_steps = epics_signal_r(float, prefix + "TOTAL_POINTS_RBV")
            self.total_time = create_r_hardware_backed_soft_signal(
                float, self._calculate_total_time
            )

            # Read per point
            self.image = epics_signal_r(Array1D[np.float64], prefix + "IMAGE")
            self.spectrum = epics_signal_r(Array1D[np.float64], prefix + "INT_SPECTRUM")
            self.total_intensity = create_r_hardware_backed_soft_signal(
                float, self._calculate_total_intensity
            )

        super().__init__(name)

    @abstractmethod
    def _get_angle_axis_signal(self, prefix: str = "") -> SignalR:
        """
        The signal that defines the angle axis. Depends on analyser model.
        """

    @abstractmethod
    def _get_energy_axis_signal(self, prefix: str = "") -> SignalR:
        """
        The signal that defines the energy axis. Depends on analyser model.
        """

    async def _calculate_binding_energy_axis(self) -> Array1D[np.float64]:
        energy_axis_values = await self.energy_axis.get_value()
        excitation_energy_value = await self.excitation_energy.get_value()
        return np.array(
            [
                to_binding_energy(
                    i_energy_axis, EnergyMode.KINETIC, excitation_energy_value
                )
                for i_energy_axis in energy_axis_values
            ]
        )

    async def _calculate_total_intensity(self) -> float:
        return np.sum(await self.spectrum.get_value())

    async def _calculate_total_time(self) -> float:
        return (
            await self.total_steps.get_value()
            * await self.step_time.get_value()
            * await self.iterations.get_value()
        )

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
