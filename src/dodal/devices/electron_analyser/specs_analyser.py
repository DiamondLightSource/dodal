import asyncio

from ophyd_async.core import AsyncStatus
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.abstract_analyser import AbstractBaseAnalyser
from dodal.devices.electron_analyser.specs_region import SpecsRegion


class SpecsAnalyser(AbstractBaseAnalyser):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.psu_mode = epics_signal_rw(str, prefix + "SCAN_RANGE")
            self.values = epics_signal_rw(int, prefix + "VALUES")
            self.centre_energy = epics_signal_rw(float, prefix + "KINETIC_ENERGY")

        super().__init__(prefix, name)

    def get_pass_energy_type(self) -> type:
        return float

    @AsyncStatus.wrap
    async def set(
        self, region: SpecsRegion, excitation_energy_eV: float, *args, **kwargs
    ):
        # These units need to be converted depending on the region
        energy_step_eV = region.get_energy_step_eV()

        await asyncio.gather(
            super().set(region, excitation_energy_eV),
            self.values.set(region.values),
            self.psu_mode.set(region.psuMode),
            (
                self.centre_energy.set(region.centreEnergy)
                if region.acquisitionMode == "Fixed Transmission"
                else asyncio.sleep(0)
            ),
            (
                self.energy_step.set(energy_step_eV)
                if region.acquisitionMode == "Fixed Energy"
                else asyncio.sleep(0)
            ),
        )
