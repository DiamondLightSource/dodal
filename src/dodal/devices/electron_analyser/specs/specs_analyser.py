from ophyd_async.epics.core import epics_signal_w

from dodal.devices.electron_analyser.base_analyser import BaseAnalyser


class SpecsAnalyser(BaseAnalyser):
    PV_PSU_MODE = "SCAN_RANGE"
    PV_VALUES = "VALUES"
    PV_CENTRE_ENERGY = "KINETIC_ENERGY"

    def __init__(self, prefix: str, name: str = "") -> None:
        self.prefix = prefix

        with self.add_children_as_readables():
            self.psu_mode_signal = epics_signal_w(
                float, self.prefix + SpecsAnalyser.PV_PSU_MODE
            )
            self.values_signal = epics_signal_w(
                float, self.prefix + SpecsAnalyser.PV_VALUES
            )
            self.centre_energy_signal = epics_signal_w(
                float, self.prefix + SpecsAnalyser.PV_CENTRE_ENERGY
            )

        super().__init__(prefix, name)
