from PIL import Image

from dodal.devices.areadetector.plugins.MJPG import MJPG

CROSSHAIR_LENGTH_PX = 20
CROSSHAIR_OUTLINE_COLOUR = "Black"
CROSSHAIR_FILL_COLOUR = "White"


class Snapshot(MJPG):
    """A child of MJPG which, when triggered, saves the image to disk."""

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ) -> None:
        super().__init__(prefix, name)

    async def post_processing(self, image: Image.Image):
        await self._save_image(image)
