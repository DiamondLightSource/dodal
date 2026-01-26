from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_rw


class PinTipCentreHolder(StandardReadable):
    """Temporary device to hold the pin tip x,y positions for centring.
    It uses the CenterX and CenterY PVs in the overlay plugin for the OAV device to
    save and read the pit tip location.

    Signals:
        pin_tip_i: x position of the pin tip, in pixels.
        pin_tip_j: y position of the pin tip, in pixels.

    This workaround is necessary because it's not yet possible to get these values back
    from a plan in blueapi. It will be removed once this is completed
    https://github.com/DiamondLightSource/blueapi/issues/1349
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        overlay_channel: int = 1,
    ):
        with self.add_children_as_readables():
            self.pin_tip_i = epics_signal_rw(
                int, prefix + f"OVER:{overlay_channel}:CenterX"
            )
            self.pin_tip_j = epics_signal_rw(
                int, prefix + f"OVER:{overlay_channel}:CenterY"
            )
        super().__init__(name)
