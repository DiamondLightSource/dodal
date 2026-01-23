from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.oav.oav_detector import OAV, BaseZoomController
from dodal.devices.oav.oav_parameters import OAVConfig


class OAVPinTipCentre(OAV):
    """"""

    def __init__(
        self,
        prefix: str,
        config: OAVConfig,
        name: str = "",
        mjpeg_prefix: str = "MJPG",
        zoom_controller: BaseZoomController | None = None,
        overlay_channel: int = 1,
    ):
        with self.add_children_as_readables():
            self.beam_centre_i = epics_signal_rw(
                int, prefix + f"OVER:{overlay_channel}:CenterX"
            )
            self.beam_centre_j = epics_signal_rw(
                int, prefix + f"OVER:{overlay_channel}:CenterY"
            )
        super().__init__(
            prefix=prefix,
            config=config,
            name=name,
            mjpeg_prefix=mjpeg_prefix,
            zoom_controller=zoom_controller,
        )
