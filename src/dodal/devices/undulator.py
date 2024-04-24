from enum import Enum

from ophyd_async.core import StandardReadable
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r

# The acceptable difference, in mm, between the undulator gap and the DCM
# energy, when the latter is converted to mm using lookup tables
UNDULATOR_DISCREPANCY_THRESHOLD_MM = 2e-3


class UndulatorGapAccess(Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class Undulator(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        lookup_table_path="/dls_sw/i03/software/daq_configuration/lookup/BeamLine_Undulator_toGap.txt",
    ) -> None:
        self.gap_motor = Motor(prefix + "BLGAPMTR")
        self.current_gap = epics_signal_r(float, prefix + "CURRGAPD")
        self.gap_access = epics_signal_r(UndulatorGapAccess, prefix + "IDBLENA")
        self.gap_discrepancy_tolerance_mm: float = UNDULATOR_DISCREPANCY_THRESHOLD_MM
        self.lookup_table_path = lookup_table_path
        self.set_readable_signals(
            read=[
                self.gap_motor,  # type: ignore
                self.current_gap,
                self.gap_access,
            ]
        )
        super().__init__(name)
