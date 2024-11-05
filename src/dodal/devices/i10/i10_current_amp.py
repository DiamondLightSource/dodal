from ophyd_async.core import Device

from dodal.devices.current_amplifiers import (
    SR570,
    Femto3xxGainTable,
    Femto3xxGainToCurrentTable,
    Femto3xxRaiseTime,
    FemtoDDPCA,
    SR570FineGainTable,
    SR570FullGainTable,
    SR570GainTable,
)


class RasorFemto(Device):
    def __init__(self, prefix: str, suffix: str = "GAIN", name: str = "") -> None:
        self.ca1 = FemtoDDPCA(
            prefix + "-01:",
            suffix=suffix,
            gain_table=Femto3xxGainTable,
            gain_to_current_table=Femto3xxGainToCurrentTable,
            raise_timetable=Femto3xxRaiseTime,
        )
        self.ca2 = FemtoDDPCA(
            prefix + "-02:",
            suffix=suffix,
            gain_table=Femto3xxGainTable,
            gain_to_current_table=Femto3xxGainToCurrentTable,
            raise_timetable=Femto3xxRaiseTime,
        )
        self.ca3 = FemtoDDPCA(
            prefix + "-03:",
            suffix=suffix,
            gain_table=Femto3xxGainTable,
            gain_to_current_table=Femto3xxGainToCurrentTable,
            raise_timetable=Femto3xxRaiseTime,
        )
        super().__init__(name)


class RasorSR370(Device):
    def __init__(self, prefix: str, suffix: str = "SENS:SEL", name: str = "") -> None:
        self.ca1 = SR570(
            prefix + "-04:",
            suffix=suffix,
            gain_table=SR570GainTable,
            fine_gain_table=SR570FineGainTable,
            full_gain_table=SR570FullGainTable,
            gain_to_current_table=Femto3xxGainToCurrentTable,
            raise_timetable=Femto3xxRaiseTime,
        )
        self.ca2 = SR570(
            prefix + "-05:",
            suffix=suffix,
            gain_table=SR570GainTable,
            fine_gain_table=SR570FineGainTable,
            full_gain_table=SR570FullGainTable,
            gain_to_current_table=Femto3xxGainToCurrentTable,
            raise_timetable=Femto3xxRaiseTime,
        )
        self.ca3 = SR570(
            prefix + "-06:",
            suffix=suffix,
            gain_table=SR570GainTable,
            fine_gain_table=SR570FineGainTable,
            full_gain_table=SR570FullGainTable,
            gain_to_current_table=Femto3xxGainToCurrentTable,
            raise_timetable=Femto3xxRaiseTime,
        )
        super().__init__(name)
