import asyncio

from ophyd_async.core import AsyncStatus
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.abstract_analyser_controller import (
    AbstractAnalyserController,
)
from dodal.devices.electron_analyser.specs_region import SpecsRegion


class SpecsAnalyserController(AbstractAnalyserController):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.psu_mode = epics_signal_rw(str, prefix + "SCAN_RANGE")
            self.values = epics_signal_rw(int, prefix + "VALUES")
            self.centre_energy = epics_signal_rw(float, prefix + "KINETIC_ENERGY")

        super().__init__(prefix, name)

    @AsyncStatus.wrap
    async def set(
        self, region: SpecsRegion, excitation_energy_eV: float, *args, **kwargs
    ):
        await asyncio.gather(
            super().set(region, excitation_energy_eV),
            self.values.set(region.values),
            self.psu_mode.set(region.psu_mode),
            (
                self.centre_energy.set(region.centre_energy)
                if region.acquisition_mode == "Fixed Transmission"
                else asyncio.sleep(0)
            ),
            (
                self.energy_step.set(region.energy_step)
                if region.acquisition_mode == "Fixed Energy"
                else asyncio.sleep(0)
            ),
        )
