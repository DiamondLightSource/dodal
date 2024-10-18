from ophyd_async.core import SignalR
from PIL import Image, ImageDraw

from dodal.devices.areadetector.plugins.MJPG_async import MJPG


class SnapshotWithBeamCentre(MJPG):
    """A child of MJPG which, when triggered, draws an outlined crosshair at the beam
    centre in the image and saves the image to disk."""

    CROSSHAIR_LENGTH_PX = 20
    CROSSHAIR_OUTLINE_COLOUR = "Black"
    CROSSHAIR_FILL_COLOUR = "White"

    def __init__(
        self,
        prefix: str,
        beam_x_signal: SignalR,
        beam_y_signal: SignalR,
        name: str = "",
    ) -> None:
        self.beam_centre_i = beam_x_signal
        self.beam_centre_j = beam_y_signal
        super().__init__(prefix, name)

    async def post_processing(self, image: Image.Image):
        print("HERE 3")
        beam_x = await self.beam_centre_i.get_value()
        beam_y = await self.beam_centre_j.get_value()
        print("HERE 4")
        SnapshotWithBeamCentre.draw_crosshair(image, beam_x, beam_y)
        print("HERE 5")

        await self._save_image(image)

    @classmethod
    def draw_crosshair(cls, image: Image.Image, beam_x: int, beam_y: int):
        draw = ImageDraw.Draw(image)
        OUTLINE_WIDTH = 1
        HALF_LEN = cls.CROSSHAIR_LENGTH_PX / 2
        draw.rectangle(
            [
                beam_x - OUTLINE_WIDTH,
                beam_y - HALF_LEN - OUTLINE_WIDTH,
                beam_x + OUTLINE_WIDTH,
                beam_y + HALF_LEN + OUTLINE_WIDTH,
            ],
            fill=cls.CROSSHAIR_OUTLINE_COLOUR,
        )
        draw.rectangle(
            [
                beam_x - HALF_LEN - OUTLINE_WIDTH,
                beam_y - OUTLINE_WIDTH,
                beam_x + HALF_LEN + OUTLINE_WIDTH,
                beam_y + OUTLINE_WIDTH,
            ],
            fill=cls.CROSSHAIR_OUTLINE_COLOUR,
        )
        draw.line(
            ((beam_x, beam_y - HALF_LEN), (beam_x, beam_y + HALF_LEN)),
            fill=cls.CROSSHAIR_FILL_COLOUR,
        )
        draw.line(
            ((beam_x - HALF_LEN, beam_y), (beam_x + HALF_LEN, beam_y)),
            fill=cls.CROSSHAIR_FILL_COLOUR,
        )
