from ophyd_async.core import StandardReadable, StandardReadableFormat

from dodal.devices.current_amplifiers import StruckScalerChannel
from dodal.devices.scaler_card import CountMode, Struck32ChannelScaler


class I10JScalerCard(StandardReadable):
    def __init__(self, prefix, name: str = "") -> None:
        self.controller = Struck32ChannelScaler(
            prefix=prefix,
            stage_mode=CountMode.ONE_SHOT,
            unstage_mode=CountMode.AUTO,
        )
        self.add_readables(
            [
                self.controller.integration_time,
                self.controller.count_mode,
                self.controller.delay_time,
            ],
            StandardReadableFormat.CONFIG_SIGNAL,
        )
        with self.add_children_as_readables():
            self.mon = StruckScalerChannel(self.controller, suffix=".S17")
            self.tey = StruckScalerChannel(self.controller, suffix=".S18")
            self.fy = StruckScalerChannel(self.controller, suffix=".S19")
            self.fy2 = StruckScalerChannel(self.controller, suffix=".S20")
        super().__init__(name)
