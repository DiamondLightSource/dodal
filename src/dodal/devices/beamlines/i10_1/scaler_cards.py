from ophyd_async.core import StandardReadable

from dodal.devices.current_amplifiers import StruckScalerChannel
from dodal.devices.scaler_card import Struck32ChannelScaler


class I10JScalerChannels(StandardReadable):
    """Channels of an i10-1 scaler card used with current amplifiers.

    To be used as the channels of a :class:`dodal.devices.scaler_card.ScalerCard`
    with the same controller.
    """

    def __init__(self, controller: Struck32ChannelScaler, name: str = "") -> None:
        with self.add_children_as_readables():
            self.mon = StruckScalerChannel(controller, suffix=".S17")
            self.tey = StruckScalerChannel(controller, suffix=".S18")
            self.fy = StruckScalerChannel(controller, suffix=".S19")
            self.fy2 = StruckScalerChannel(controller, suffix=".S20")
        super().__init__(name)
