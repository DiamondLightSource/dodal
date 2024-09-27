from enum import Enum

from ophyd_async.core import (
    ConfigSignal,
    StandardReadable,
)
from ophyd_async.epics.motor import Motor
from ophyd_async.epics.signal import epics_signal_rw


class PGM(StandardReadable):
    """
    Plane grating monochromator, it is use in soft x-ray beamline to generate monochromic beam.
    """

    def __init__(
        self,
        prefix: str,
        grating: type[Enum],
        gratingPv: str,
        name: str = "",
    ) -> None:
        """
        Parameters
        ----------
        prefix:
            Beamline specific part of the PV
        grating:
            The Enum for the grating table.
        gratingPv:
            The suffix pv part of grating Pv
        name:
            Name of the device
        """
        with self.add_children_as_readables():
            self.energy = Motor(prefix + "ENERGY")
        with self.add_children_as_readables(ConfigSignal):
            self.grating = epics_signal_rw(grating, prefix + gratingPv)
            self.cff = epics_signal_rw(float, prefix + "CFF")

        super().__init__(name=name)
