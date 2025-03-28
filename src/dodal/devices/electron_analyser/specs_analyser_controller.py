from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.electron_analyser.abstract_analyser_controller import (
    AbstractAnalyserController,
)


class SpecsAnalyserController(AbstractAnalyserController):
    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(prefix, name)
        with self.add_children_as_readables():
            self.psu_mode = epics_signal_rw(str, prefix + "SCAN_RANGE")
            self.values = epics_signal_rw(int, prefix + "VALUES")
            self.centre_energy = epics_signal_rw(float, prefix + "KINETIC_ENERGY")
