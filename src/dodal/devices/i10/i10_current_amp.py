from ophyd_async.core import Device

from dodal.devices.current_amplifiers import (
    Femto3xxGainTable,
    Femto3xxRaiseTime,
    FemtoDDPCA,
)


class RasorFemto(Device):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.ca1 = FemtoDDPCA(
            prefix + "-01:",
            gain_table=Femto3xxGainTable,
            raise_timetable=Femto3xxRaiseTime,
        )
        self.ca2 = FemtoDDPCA(
            prefix + "-02:",
            gain_table=Femto3xxGainTable,
            raise_timetable=Femto3xxRaiseTime,
        )
        self.ca3 = FemtoDDPCA(
            prefix + "-03:",
            gain_table=Femto3xxGainTable,
            raise_timetable=Femto3xxRaiseTime,
        )

        super().__init__(name)
