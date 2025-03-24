import asyncio
from abc import abstractmethod
from typing import Generic, TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.abstract_region import (
    EnergyMode,
    TAbstractBaseRegion,
)
from dodal.log import LOGGER


class AbstractBaseAnalyser(StandardReadable, Movable, Generic[TAbstractBaseRegion]):
    """
    Generic device to configure electron analyser with new region settings.
    Electron analysers should inherit from this class if they need further
    specialisation.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.low_energy = epics_signal_rw(float, prefix + "LOW_ENERGY")
            self.high_energy = epics_signal_rw(float, prefix + "HIGH_ENERGY")
            self.slices = epics_signal_rw(int, prefix + "SLICES")
            self.lens_mode = epics_signal_rw(str, prefix + "LENS_MODE")
            self.pass_energy = epics_signal_rw(
                self.get_pass_energy_type(), prefix + "PASS_ENERGY"
            )
            self.energy_step = epics_signal_rw(float, prefix + "STEP_SIZE")
            self.iterations = epics_signal_rw(int, prefix + "NumExposures")
            self.acquisition_mode = epics_signal_rw(str, prefix + "ACQ_MODE")

        super().__init__(name)

    @abstractmethod
    def get_pass_energy_type(self) -> type:
        pass

    def to_kinetic_energy(
        self, value: float, excitation_energy_eV: float, mode: EnergyMode
    ) -> float:
        return excitation_energy_eV - value if mode == EnergyMode.BINDING else value

    @AsyncStatus.wrap
    async def set(
        self,
        value: TAbstractBaseRegion,
        excitation_energy_eV: float | None = None,
        *args,
        **kwargs,
    ):
        """
        This is intended to be used with bluesky plan
        bps.abs_set(analyser, region, excitation_energy)
        """

        region = value
        if excitation_energy_eV is None:
            raise ValueError("excitation_energy_eV must be specified.")

        LOGGER.info(f'Configuring analyser with region "{region.name}"')
        low_energy = region.to_kinetic_energy(region.lowEnergy, excitation_energy_eV)
        high_energy = region.to_kinetic_energy(region.highEnergy, excitation_energy_eV)
        # Cast pass energy to correct type for PV to take
        pass_energy_type = self.get_pass_energy_type()
        pass_energy = pass_energy_type(region.passEnergy)
        # Set detector settings, wait for them all to have completed
        await asyncio.gather(
            self.low_energy.set(low_energy),
            self.high_energy.set(high_energy),
            self.slices.set(region.slices),
            self.lens_mode.set(region.lensMode),
            self.pass_energy.set(pass_energy),
            self.iterations.set(region.iterations),
            self.acquisition_mode.set(region.acquisitionMode),
        )


TAbstractBaseAnalyser = TypeVar("TAbstractBaseAnalyser", bound=AbstractBaseAnalyser)
