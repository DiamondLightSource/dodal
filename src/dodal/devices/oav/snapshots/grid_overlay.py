from enum import Enum
from functools import partial

from PIL import Image, ImageDraw


class Orientation(Enum):
    horizontal = 0
    vertical = 1


def _add_parallel_lines_to_image(
    image: Image.Image,
    start_x: int,
    start_y: int,
    line_length: int,
    spacing: float,
    num_lines: int,
    orientation=Orientation.horizontal,
):
    """Draws horizontal or vertical parallel lines on a given image.
    Draws a line of a given length and orientation starting from a given point; then \
    draws a given number of parallel lines equally spaced with a given spacing. \
    If the line is horizontal, the start point corresponds to left end of the initial \
    line and the other parallel lines will be drawn below the initial line; if \
    vertical, the start point corresponds to the top end of the initial line and the \
    other parallel lines will be drawn to the right of the initial line. (0,0) is the \
    top left of the image.

    Args:
        image (PIL.Image): The image to be drawn upon.
        start_x (int): The x coordinate (in pixels) of the start of the initial line.
        start_y (int): The y coordinate (in pixels) of the start of the initial line.
        line_length (int): The length of each of the parallel lines in pixels.
        spacing (float): The spacing, in pixels, between each parallel line. Strictly, \
            there are spacing-1 pixels between each line
        num_lines (int): The total number of parallel lines to draw.
        orientation (Orientation): The orientation (horizontal or vertical) of the \
            parallel lines to draw."""
    lines = [
        (
            (
                (start_x, start_y + int(i * spacing)),
                (start_x + line_length, start_y + int(i * spacing)),
            )
            if orientation == Orientation.horizontal
            else (
                (start_x + int(i * spacing), start_y),
                (start_x + int(i * spacing), start_y + line_length),
            )
        )
        for i in range(num_lines)
    ]
    draw = ImageDraw.Draw(image)
    for line in lines:
        draw.line(line)


_add_vertical_parallel_lines_to_image = partial(
    _add_parallel_lines_to_image, orientation=Orientation.vertical
)


_add_horizontal_parallel_lines_to_image = partial(
    _add_parallel_lines_to_image, orientation=Orientation.horizontal
)


def add_grid_border_overlay_to_image(
    image: Image.Image,
    top_left_x: int,
    top_left_y: int,
    box_width: float,
    num_boxes_x: int,
    num_boxes_y: int,
):
    _add_vertical_parallel_lines_to_image(
        image,
        start_x=top_left_x,
        start_y=top_left_y,
        line_length=int(num_boxes_y * box_width),
        spacing=int(num_boxes_x * box_width),
        num_lines=2,
    )
    _add_horizontal_parallel_lines_to_image(
        image,
        start_x=top_left_x,
        start_y=top_left_y,
        line_length=int(num_boxes_x * box_width),
        spacing=int(num_boxes_y * box_width),
        num_lines=2,
    )


def add_grid_overlay_to_image(
    image: Image.Image,
    top_left_x: int,
    top_left_y: int,
    box_width: float,
    num_boxes_x: int,
    num_boxes_y: int,
):
    _add_vertical_parallel_lines_to_image(
        image,
        start_x=int(top_left_x + box_width),
        start_y=top_left_y,
        line_length=int(num_boxes_y * box_width),
        spacing=box_width,
        num_lines=num_boxes_x - 1,
    )
    _add_horizontal_parallel_lines_to_image(
        image,
        start_x=top_left_x,
        start_y=int(top_left_y + box_width),
        line_length=int(num_boxes_x * box_width),
        spacing=box_width,
        num_lines=num_boxes_y - 1,
    )
