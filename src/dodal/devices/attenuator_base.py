from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_x


class AttenuatorBase(StandardReadable):
    """An attenuator base class with a minimum set of common PVs to phase1 beamlines."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self._desired_transmission = epics_signal_rw(float, prefix + "T2A:SETVAL1")
        self._use_current_energy = epics_signal_x(prefix + "E2WL:USECURRENTENERGY.PROC")

        with self.add_children_as_readables():
            self.actual_transmission = epics_signal_r(float, prefix + "MATCH")

        super().__init__(name)
