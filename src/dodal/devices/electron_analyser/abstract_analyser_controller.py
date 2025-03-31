from abc import ABC
from typing import TypeVar

import numpy as np
from ophyd_async.core import Array1D, StandardReadable
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.abstract_region import EnergyMode


class AbstractAnalyserController(ABC, StandardReadable):
    """
    Generic device to configure electron analyser with new region settings.
    Electron analysers should inherit from this class for further specialisation.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            # Used for setting up region data acuqisition
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

            self.step_time = epics_signal_r(float, prefix + "AcquireTime_RBV")
            self.total_steps = epics_signal_r(float, prefix + "TOTAL_POINTS_RBV")

        super().__init__(name)

    async def total_intensity(self) -> float:
        spectrum_data = await self.spectrum.get_value()
        return np.sum(spectrum_data)


TAbstractAnalyserController = TypeVar(
    "TAbstractAnalyserController", bound=AbstractAnalyserController
)
