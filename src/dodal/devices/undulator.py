from enum import Enum

from ophyd import Component, Device, EpicsMotor, EpicsSignalRO

UNDULATOR_DISCREPANCY_THRESHOLD = 1e-3  # This property was read from GDA although it didn't appear to exist anywhere, it defaults to this value


class UndulatorGapAccess(Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class Undulator(Device):
    gap_motor: EpicsMotor = Component(EpicsMotor, "BLGAPMTR")
    current_gap: EpicsSignalRO = Component(EpicsSignalRO, "CURRGAPD")
    gap_access: EpicsSignalRO = Component(EpicsSignalRO, "IDBLENA")
    lookup_table_path: str = (
        "/dls_sw/i03/software/daq_configuration/lookup/BeamLine_Undulator_toGap.txt"
    )
    gap_discrepancy_tolerance: float = UNDULATOR_DISCREPANCY_THRESHOLD
