from enum import Enum

from ophyd_async.core import StandardReadable
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r

# The acceptable difference, in mm, between the undulator gap and the DCM
# energy, when the latter is converted to mm using lookup tables
UNDULATOR_DISCREPANCY_THRESHOLD_MM = 2e-3


class UndulatorGapAccess(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class Undulator(StandardReadable):
    """
    An Undulator-type insertion device, used to control photon emission at a given
    beam energy.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.gap_motor = Motor(prefix + "BLGAPMTR")
            self.current_gap = epics_signal_r(float, prefix + "CURRGAPD")
            self.gap_access = epics_signal_r(UndulatorGapAccess, prefix + "IDBLENA")
        self.gap_discrepancy_tolerance_mm: float = UNDULATOR_DISCREPANCY_THRESHOLD_MM

        super().__init__(name)
