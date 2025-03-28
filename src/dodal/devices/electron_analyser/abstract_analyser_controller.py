from abc import ABC
from typing import Generic, TypeVar

from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.abstract_region import (
    EnergyMode,
    TAbstractBaseRegion,
)


class AbstractAnalyserController(ABC, StandardReadable, Generic[TAbstractBaseRegion]):
    """
    Generic device to configure electron analyser with new region settings.
    Electron analysers should inherit from this class for further specialisation.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.low_energy = epics_signal_rw(float, prefix + "LOW_ENERGY")
            self.high_energy = epics_signal_rw(float, prefix + "HIGH_ENERGY")
            self.slices = epics_signal_rw(int, prefix + "SLICES")
            self.lens_mode = epics_signal_rw(str, prefix + "LENS_MODE")
            self.pass_energy = epics_signal_rw(str, prefix + "PASS_ENERGY")
            self.energy_step = epics_signal_rw(float, prefix + "STEP_SIZE")
            self.iterations = epics_signal_rw(int, prefix + "NumExposures")
            self.acquisition_mode = epics_signal_rw(str, prefix + "ACQ_MODE")

        super().__init__(name)

    def to_kinetic_energy(
        self, value: float, excitation_energy: float, mode: EnergyMode
    ) -> float:
        return excitation_energy - value if mode == EnergyMode.BINDING else value


TAbstractAnalyserController = TypeVar(
    "TAbstractAnalyserController", bound=AbstractAnalyserController
)
