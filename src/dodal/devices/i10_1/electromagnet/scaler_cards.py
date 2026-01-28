from ophyd_async.core import Device

from dodal.devices.current_amplifiers import StruckScaler


class ElectromagnetScalerCard1(Device):
    def __init__(self, prefix, name: str = "") -> None:
        self.mon = StruckScaler(prefix=prefix, suffix=".S17")
        self.tey = StruckScaler(prefix=prefix, suffix=".S18")
        self.fy = StruckScaler(prefix=prefix, suffix=".S19")
        self.fy2 = StruckScaler(prefix=prefix, suffix=".S20")
        super().__init__(name)
