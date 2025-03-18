import asyncio
from typing import Generic, TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.base_region import EnergyMode, TBaseRegion
from dodal.log import LOGGER


class BaseAnalyser(StandardReadable, Movable, Generic[TBaseRegion]):
    """
    Generic device to configure electron analyser with new region settings.
    Electron analysers should inherit from this class if they need further
    specialisation.
    """

    PV_LENS_MODE = "LENS_MODE"
    PV_PASS_ENERGY = "PASS_ENERGY"
    PV_ACQISITION_MODE = "ACQ_MODE"
    PV_LOW_ENERGY = "LOW_ENERGY"
    PV_HIGH_ENERGY = "HIGH_ENERGY"
    PV_SLICES = "SLICES"
    PV_ITERATIONS = "NumExposures"
    PV_ENERGY_STEP = "STEP_SIZE"

    def __init__(self, prefix: str, name: str = "") -> None:
        self.prefix = prefix

        with self.add_children_as_readables():
            self.low_energy_signal = epics_signal_rw(
                float, self.prefix + BaseAnalyser.PV_LOW_ENERGY
            )
            self.high_energy_signal = epics_signal_rw(
                float, self.prefix + BaseAnalyser.PV_HIGH_ENERGY
            )

            self.slices_signal = epics_signal_rw(
                int, self.prefix + BaseAnalyser.PV_SLICES
            )
            self.lens_mode_signal = epics_signal_rw(
                str, self.prefix + BaseAnalyser.PV_LENS_MODE
            )
            self.pass_energy_signal = epics_signal_rw(
                self.get_pass_energy_type(), self.prefix + BaseAnalyser.PV_PASS_ENERGY
            )
            self.energy_step_signal = epics_signal_rw(
                float, self.prefix + BaseAnalyser.PV_ENERGY_STEP
            )

            self.iterations_signal = epics_signal_rw(
                int, self.prefix + BaseAnalyser.PV_ITERATIONS
            )

            self.acquisition_mode_signal = epics_signal_rw(
                str, self.prefix + BaseAnalyser.PV_ACQISITION_MODE
            )

        super().__init__(name)

    def get_pass_energy_type(self) -> type:
        return float

    @AsyncStatus.wrap
    async def set(
        self,
        value: TBaseRegion,
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

        LOGGER.info(f"Configuring analyser with region {region.name}")

        is_binding_energy = region.energyMode == EnergyMode.BINDING
        low_energy = (
            excitation_energy_eV - region.highEnergy
            if is_binding_energy
            else region.lowEnergy
        )
        high_energy = (
            excitation_energy_eV - region.lowEnergy
            if is_binding_energy
            else region.highEnergy
        )
        # Cast pass energy to correct type for PV to take
        pass_energy_type = self.get_pass_energy_type()
        pass_energy = pass_energy_type(region.passEnergy)
        # Set detector settings, wait for them all to have completed
        await asyncio.gather(
            self.low_energy_signal.set(low_energy),
            self.high_energy_signal.set(high_energy),
            self.slices_signal.set(region.slices),
            self.lens_mode_signal.set(region.lensMode),
            self.pass_energy_signal.set(pass_energy),
            self.iterations_signal.set(region.iterations),
            self.acquisition_mode_signal.set(region.acquisitionMode),
        )


TBaseAnalyser = TypeVar("TBaseAnalyser", bound=BaseAnalyser)
