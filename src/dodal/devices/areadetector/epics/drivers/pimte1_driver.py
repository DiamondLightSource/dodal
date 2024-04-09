from enum import Enum

from ophyd_async.epics.areadetector.drivers.ad_base import ADBase
from ophyd_async.epics.areadetector.utils import ad_r, ad_rw
from ophyd_async.epics.signal import epics_signal_rw


class Pimte1Driver(ADBase):
    def __init__(self, prefix: str) -> None:
        self.trigger_mode = ad_rw(Pimte1Driver.TriggerMode, prefix + "TriggerMode")
        self.initialize = ad_rw(int, prefix + "Initialize")
        self.set_temperture = epics_signal_rw(float, prefix + "SetTemperature")
        self.read_backtemperture = ad_r(float, prefix + "MeasuredTemperature")
        self.speed = ad_rw(Pimte1Driver.SpeedMode, prefix + "SpeedSelection")
        super().__init__(prefix)

    class SpeedMode(str, Enum):
        adc_50Khz = "0: 50 KHz - 20000 ns"
        adc_100Khz = "1: 100 kHz - 10000 ns"
        adc_200Khz = "2: 200 kHz - 5000 ns"
        adc_500Khz = "3: 500 kHz - 2000 ns"
        adc_1Mhz = "4: 1 MHz - 1000 ns"
        adc_2Mhz = "5: 2 MHz - 500 ns"

    class TriggerMode(str, Enum):
        internal = "Free Run"
        ext_trigger = "Ext Trigger"
        bulb_mode = "Bulb Mode"
