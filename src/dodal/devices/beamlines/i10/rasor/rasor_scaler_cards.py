from ophyd_async.core import StandardReadable

from dodal.devices.current_amplifiers import StruckScalerChannel
from dodal.devices.scaler_card import Struck32ChannelScaler


class RasorScalerChannels(StandardReadable):
    """Channels of the RASOR scaler card used with current amplifiers.

    To be used as the channels of a :class:`dodal.devices.scaler_card.ScalerCard`
    with the same controller.
    """

    def __init__(self, controller: Struck32ChannelScaler, name: str = "") -> None:
        with self.add_children_as_readables():
            self.mon = StruckScalerChannel(controller, suffix=".S17")
            self.det = StruckScalerChannel(controller, suffix=".S18")
            self.fluo = StruckScalerChannel(controller, suffix=".S19")
            self.drain = StruckScalerChannel(controller, suffix=".S20")
        super().__init__(name)
