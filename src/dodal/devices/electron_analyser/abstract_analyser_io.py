from abc import ABC, abstractmethod
from typing import TypeVar

import numpy as np
from ophyd_async.core import Array1D, SignalR, StandardReadable
from ophyd_async.epics.adcore import ADBaseIO
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.signal_utils import create_r_hardware_backed_soft_signal
from dodal.devices.electron_analyser.abstract_region import EnergyMode
from dodal.devices.electron_analyser.util import to_binding_energy


class AbstractAnalyserDriverIO(ABC, StandardReadable):
    """
    Generic device to configure electron analyser with new region settings.
    Electron analysers should inherit from this class for further specialisation.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.adbase_cam = ADBaseIO(prefix, "adbase")

        with self.add_children_as_readables():
            self.low_energy = epics_signal_rw(float, prefix + "LOW_ENERGY")
            self.high_energy = epics_signal_rw(float, prefix + "HIGH_ENERGY")
            self.slices = epics_signal_rw(int, prefix + "SLICES")
            self.lens_mode = epics_signal_rw(str, prefix + "LENS_MODE")
            self.pass_energy = epics_signal_rw(str, prefix + "PASS_ENERGY")
            self.energy_step = epics_signal_rw(float, prefix + "STEP_SIZE")
            self.iterations = epics_signal_rw(int, prefix + "NumExposures")
            self.acquisition_mode = epics_signal_rw(str, prefix + "ACQ_MODE")

            # Used to read detector data after acqusition
            self.image = epics_signal_r(Array1D[np.float64], prefix + "IMAGE")
            self.spectrum = epics_signal_r(Array1D[np.float64], prefix + "INT_SPECTRUM")
            self.energy_axis = self._get_energy_axis_signal(prefix)
            self.angle_axis = self._get_angle_axis_signal(prefix)
            self.total_intensity = create_r_hardware_backed_soft_signal(
                float, self._calculate_total_intensity
            )
            self.step_time = epics_signal_r(float, self.adbase_cam.acquire_time.name)
            self.total_steps = epics_signal_r(float, prefix + "TOTAL_POINTS_RBV")

        super().__init__(name)

    @abstractmethod
    def _get_angle_axis_signal(self, prefix) -> SignalR:
        pass

    @abstractmethod
    def _get_energy_axis_signal(self, prefix) -> SignalR:
        pass

    async def binding_energy_axis_values(
        self, excitation_energy: float
    ) -> Array1D[np.float64]:
        energy_axis_values = await self.energy_axis.get_value()
        return np.array(
            to_binding_energy(energy_value, EnergyMode.KINETIC, excitation_energy)
            for energy_value in energy_axis_values
        )

    async def _calculate_total_intensity(self) -> float:
        return np.sum(await self.spectrum.get_value())


TAbstractAnalyserDriverIO = TypeVar(
    "TAbstractAnalyserDriverIO", bound=AbstractAnalyserDriverIO
)
