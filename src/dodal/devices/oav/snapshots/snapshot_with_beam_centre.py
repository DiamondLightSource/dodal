from ophyd_async.core import Reference, SignalR
from PIL import Image

from dodal.devices.areadetector.plugins.MJPG import MJPG

CROSSHAIR_LENGTH_PX = 20
CROSSHAIR_OUTLINE_COLOUR = "Black"
CROSSHAIR_FILL_COLOUR = "White"


class SnapshotWithBeamCentre(MJPG):
    """A child of MJPG which, when triggered, saves the image to disk."""

    def __init__(
        self,
        prefix: str,
        beam_x_signal: SignalR,
        beam_y_signal: SignalR,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self._beam_centre_i_ref = Reference(beam_x_signal)
            self._beam_centre_j_ref = Reference(beam_y_signal)
        super().__init__(prefix, name)

    async def post_processing(self, image: Image.Image):
        await self._save_image(image)
