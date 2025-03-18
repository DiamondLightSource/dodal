import asyncio

from ophyd_async.core import AsyncStatus
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.base_analyser import BaseAnalyser
from dodal.devices.electron_analyser.specs.specs_region import SpecsRegion


class SpecsAnalyser(BaseAnalyser):
    PV_PSU_MODE = "SCAN_RANGE"
    PV_VALUES = "VALUES"
    PV_CENTRE_ENERGY = "KINETIC_ENERGY"

    def __init__(self, prefix: str, name: str = "") -> None:
        self.prefix = prefix

        with self.add_children_as_readables():
            self.psu_mode_signal = epics_signal_rw(
                str, self.prefix + SpecsAnalyser.PV_PSU_MODE
            )
            self.values_signal = epics_signal_rw(
                int, self.prefix + SpecsAnalyser.PV_VALUES
            )
            self.centre_energy_signal = epics_signal_rw(
                float, self.prefix + SpecsAnalyser.PV_CENTRE_ENERGY
            )

        super().__init__(prefix, name)

    @AsyncStatus.wrap
    async def set(
        self, value: SpecsRegion, excitation_energy_eV: float, *args, **kwargs
    ):
        region = value
        # These units need to be converted depending on the region
        energy_step_eV = region.get_energy_step_eV()

        await asyncio.gather(
            super().set(region, excitation_energy_eV),
            self.values_signal.set(region.values),
            self.psu_mode_signal.set(region.psuMode),
            self.centre_energy_signal.set(region.centreEnergy)
            if region.acquisitionMode == "Fixed Transmission"
            else asyncio.sleep(0),
            self.energy_step_signal.set(energy_step_eV)
            if region.acquisitionMode == "Fixed Energy"
            else asyncio.sleep(0),
        )
