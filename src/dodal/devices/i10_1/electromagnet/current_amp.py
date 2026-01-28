from ophyd_async.core import Device

from dodal.devices.current_amplifiers import (
    SR570,
    SR570FineGainTable,
    SR570FullGainTable,
    SR570GainTable,
    SR570GainToCurrentTable,
    SR570RaiseTimeTable,
)


class ElectromagnetSR570(Device):
    def __init__(self, prefix: str, suffix: str = "SENS:SEL", name: str = "") -> None:
        self.ca1 = SR570(
            prefix + "-08:",
            suffix=suffix,
            fine_gain_table=SR570FineGainTable,
            coarse_gain_table=SR570GainTable,
            combined_table=SR570FullGainTable,
            gain_to_current_table=SR570GainToCurrentTable,
            raise_timetable=SR570RaiseTimeTable,
        )
        self.ca2 = SR570(
            prefix + "-09:",
            suffix=suffix,
            fine_gain_table=SR570FineGainTable,
            coarse_gain_table=SR570GainTable,
            combined_table=SR570FullGainTable,
            gain_to_current_table=SR570GainToCurrentTable,
            raise_timetable=SR570RaiseTimeTable,
        )
        super().__init__(name)
