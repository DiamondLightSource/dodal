from enum import Enum

from ophyd import Component, Device, EpicsMotor, EpicsSignalRO

# The acceptable difference, in mm, between the undulator gap and the DCM
# energy, when the latter is converted to mm using lookup tables
UNDULATOR_DISCREPANCY_THRESHOLD_MM = 2e-3


class UndulatorGapAccess(Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class Undulator(Device):
    gap_motor = Component(EpicsMotor, "BLGAPMTR")
    current_gap = Component(EpicsSignalRO, "CURRGAPD")
    gap_access = Component(EpicsSignalRO, "IDBLENA")
    gap_discrepancy_tolerance_mm: float = UNDULATOR_DISCREPANCY_THRESHOLD_MM

    def __init__(
        self,
        lookup_table_path="/dls_sw/i03/software/daq_configuration/lookup/BeamLine_Undulator_toGap.txt",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.lookup_table_path = lookup_table_path
