from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_x

# This will need a set
# See https://github.com/DiamondLightSource/dodal/issues/928


class AttenuatorBase(StandardReadable):
    """An attenuator base class with a minimum set of common PVs to phase1 beamlines.

    The desired transmission value is fractional (i.e 0-1) instead of a percentage, \
    and when read from the device the actual_transmission will also return a fraction.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self._desired_transmission = epics_signal_rw(float, prefix + "T2A:SETVAL1")
        self._use_current_energy = epics_signal_x(prefix + "E2WL:USECURRENTENERGY.PROC")

        with self.add_children_as_readables():
            self.actual_transmission = epics_signal_r(float, prefix + "MATCH")

        super().__init__(name)
