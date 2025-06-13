from PIL import Image, ImageDraw

from dodal.devices.oav.utils import Pixel

CROSSHAIR_LENGTH_PX = 20
CROSSHAIR_OUTLINE_COLOUR = "Black"
CROSSHAIR_FILL_COLOUR = "White"


def draw_crosshair(image: Image.Image, beam_x: int, beam_y: int):
    """
    Draw a crosshair at the beam centre coordinates specified.
    Args:
        image: The image to draw the crosshair onto. This is mutated.
        beam_x: The x-coordinate of the crosshair (pixels)
        beam_y: The y-coordinate of the crosshair (pixels)
    """
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


def compute_beam_centre_pixel_xy_for_mm_position(
    sample_pos_mm: tuple[float, float],
    beam_pos_at_origin_px: Pixel,
    microns_per_pixel: tuple[float, float],
) -> Pixel:
    """
    Compute the location of the beam centre in pixels on a reference image.
    Args:
        sample_pos_mm: x, y location of the sample in mm relative to when the reference image
            was taken.
        beam_pos_at_origin_px: x, y position of the beam centre in the reference image (pixels)
        microns_per_pixel: x, y scaling factor relating the sample position to the position in the image.
    Returns:
        x, y location of the beam centre (pixels)

    """

    def centre(sample_pos, beam_pos, um_per_px) -> int:
        return beam_pos + sample_pos * 1000 / um_per_px

    return Pixel(
        centre(sp, bp, mpp)
        for sp, bp, mpp in zip(
            sample_pos_mm, beam_pos_at_origin_px, microns_per_pixel, strict=True
        )
    )
