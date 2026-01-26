from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_rw


class PinTipCentreHolder(StandardReadable):
    """"""

    def __init__(
        self,
        prefix: str,
        name: str = "",
        overlay_channel: int = 1,
    ):
        with self.add_children_as_readables():
            self.beam_centre_i = epics_signal_rw(
                int, prefix + f"OVER:{overlay_channel}:CenterX"
            )
            self.beam_centre_j = epics_signal_rw(
                int, prefix + f"OVER:{overlay_channel}:CenterY"
            )
        super().__init__(name)
