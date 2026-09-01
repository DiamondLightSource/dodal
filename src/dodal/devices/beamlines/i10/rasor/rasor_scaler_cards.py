from ophyd_async.core import Device

from dodal.devices.current_amplifiers import StruckScaler


class RasorScalerCard1(Device):
    def __init__(self, prefix, name: str = "") -> None:
        self.mon = StruckScaler(prefix=prefix, suffix=".S17")
        self.det = StruckScaler(prefix=prefix, suffix=".S18")
        self.fluo = StruckScaler(prefix=prefix, suffix=".S19")
        self.drain = StruckScaler(prefix=prefix, suffix=".S20")
        super().__init__(name)
