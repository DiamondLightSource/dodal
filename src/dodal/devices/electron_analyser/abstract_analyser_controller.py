import asyncio
from abc import ABC
from typing import Generic, TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.abstract_region import (
    EnergyMode,
    TAbstractBaseRegion,
)
from dodal.log import LOGGER


class AbstractAnalyserController(
    ABC, StandardReadable, Movable, Generic[TAbstractBaseRegion]
):
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
        self, value: float, excitation_energy_eV: float, mode: EnergyMode
    ) -> float:
        return excitation_energy_eV - value if mode == EnergyMode.BINDING else value

    @AsyncStatus.wrap
    async def set(
        self,
        region: TAbstractBaseRegion,
        excitation_energy_eV: float,
        *args,
        **kwargs,
    ):
        """
        This is intended to be used with bluesky plan
        bps.abs_set(analyser, region, excitation_energy)
        """

        LOGGER.info(f'Configuring analyser with region "{region.name}"')
        low_energy = region.to_kinetic_energy(region.lowEnergy, excitation_energy_eV)
        high_energy = region.to_kinetic_energy(region.highEnergy, excitation_energy_eV)
        # Set detector settings, wait for them all to have completed
        await asyncio.gather(
            self.low_energy.set(low_energy),
            self.high_energy.set(high_energy),
            self.slices.set(region.slices),
            self.lens_mode.set(region.lensMode),
            self.pass_energy.set(region.passEnergy),
            self.iterations.set(region.iterations),
            self.acquisition_mode.set(region.acquisitionMode),
        )


TAbstractAnalyserController = TypeVar(
    "TAbstractAnalyserController", bound=AbstractAnalyserController
)
