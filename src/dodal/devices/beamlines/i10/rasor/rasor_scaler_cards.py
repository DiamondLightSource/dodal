from ophyd_async.core import Device

from dodal.devices.current_amplifiers import StruckScalerChannel
from dodal.devices.scaler_card import CountMode, Struck32ChannelScaler


class RasorScalerCard1(Device):
    def __init__(self, prefix, name: str = "") -> None:
        self.controller = Struck32ChannelScaler(
            prefix=prefix,
            stage_mode=CountMode.ONE_SHOT,
            unstage_mode=CountMode.AUTO,
        )
        self.mon = StruckScalerChannel(self.controller, suffix=".S17")
        self.det = StruckScalerChannel(self.controller, suffix=".S18")
        self.fluo = StruckScalerChannel(self.controller, suffix=".S19")
        self.drain = StruckScalerChannel(self.controller, suffix=".S20")
        super().__init__(name)
