from PIL import Image, ImageDraw

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
    beam_pos_at_origin_px: tuple[int, int],
    microns_per_pixel: tuple[float, float],
) -> tuple[int, int]:
    def centre(sample_pos, beam_pos, um_per_px) -> int:
        return beam_pos + sample_pos * 1000 / um_per_px

    return tuple(
        centre(sp, bp, mpp)
        for sp, bp, mpp in zip(
            sample_pos_mm, beam_pos_at_origin_px, microns_per_pixel, strict=True
        )
    )  # type: ignore
