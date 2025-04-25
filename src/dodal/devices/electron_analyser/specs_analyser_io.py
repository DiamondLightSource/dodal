from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.abstract_analyser_io import (
    AbstractAnalyserDriverIO,
)


class SpecsAnalyserDriverIO(AbstractAnalyserDriverIO):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.psu_mode = epics_signal_rw(str, prefix + "SCAN_RANGE")
            self.values = epics_signal_rw(int, prefix + "VALUES")
            self.centre_energy = epics_signal_rw(float, prefix + "KINETIC_ENERGY")

        super().__init__(prefix, name)

    @property
    def pass_energy_type(self) -> type:
        return float
