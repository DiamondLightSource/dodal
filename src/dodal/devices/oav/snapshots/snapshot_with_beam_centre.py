from ophyd_async.core import Reference, SignalR
from PIL import Image, ImageDraw

from dodal.devices.areadetector.plugins.MJPG import MJPG

CROSSHAIR_LENGTH_PX = 20
CROSSHAIR_OUTLINE_COLOUR = "Black"
CROSSHAIR_FILL_COLOUR = "White"


def draw_crosshair(image: Image.Image, beam_x: int, beam_y: int):
    draw = ImageDraw.Draw(image)
    OUTLINE_WIDTH = 1
    HALF_LEN = CROSSHAIR_LENGTH_PX / 2
    draw.rectangle(
        [
            beam_x - OUTLINE_WIDTH,
            beam_y - HALF_LEN - OUTLINE_WIDTH,
            beam_x + OUTLINE_WIDTH,
            beam_y + HALF_LEN + OUTLINE_WIDTH,
        ],
        fill=CROSSHAIR_OUTLINE_COLOUR,
    )
    draw.rectangle(
        [
            beam_x - HALF_LEN - OUTLINE_WIDTH,
            beam_y - OUTLINE_WIDTH,
            beam_x + HALF_LEN + OUTLINE_WIDTH,
            beam_y + OUTLINE_WIDTH,
        ],
        fill=CROSSHAIR_OUTLINE_COLOUR,
    )
    draw.line(
        ((beam_x, beam_y - HALF_LEN), (beam_x, beam_y + HALF_LEN)),
        fill=CROSSHAIR_FILL_COLOUR,
    )
    draw.line(
        ((beam_x - HALF_LEN, beam_y), (beam_x + HALF_LEN, beam_y)),
        fill=CROSSHAIR_FILL_COLOUR,
    )


class SnapshotWithBeamCentre(MJPG):
    """A child of MJPG which, when triggered, draws an outlined crosshair at the beam
    centre in the image and saves the image to disk."""

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
        beam_x = await self._beam_centre_i_ref().get_value()
        beam_y = await self._beam_centre_j_ref().get_value()
        draw_crosshair(image, beam_x, beam_y)

        await self._save_image(image)
