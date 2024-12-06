from ophyd_async.core import Device

from dodal.devices.current_amplifiers import StruckScaler


class RasorScalerCard1(Device):
    def __init__(self, prefix, name: str = "") -> None:
        self.mon = StruckScaler(prefix=prefix, suffix=".16")
        self.det = StruckScaler(prefix=prefix, suffix=".17")
        self.fluo = StruckScaler(prefix=prefix, suffix=".18")
        self.drain = StruckScaler(prefix=prefix, suffix=".19")
        super().__init__(name)
