from enum import Enum
from functools import partial
from os.path import join as path_join

from ophyd import Component, Signal
from PIL import Image, ImageDraw

from dodal.devices.areadetector.plugins.MJPG import MJPG
from dodal.log import LOGGER


class Orientation(Enum):
    horizontal = 0
    vertical = 1


def _add_parallel_lines_to_image(
    image: Image,
    start_x: int,
    start_y: int,
    line_length: int,
    spacing: int,
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
        spacing (int): The spacing, in pixels, between each parallel line. Strictly, \
            there are spacing-1 pixels between each line
        num_lines (int): The total number of parallel lines to draw.
        orientation (Orientation): The orientation (horizontal or vertical) of the \
            parallel lines to draw."""
    lines = [
        (
            (start_x, start_y + i * spacing),
            (start_x + line_length, start_y + i * spacing),
        )
        if orientation == Orientation.horizontal
        else (
            (start_x + i * spacing, start_y),
            (start_x + i * spacing, start_y + line_length),
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
    box_width: int,
    num_boxes_x: int,
    num_boxes_y: int,
):
    _add_vertical_parallel_lines_to_image(
        image,
        start_x=top_left_x,
        start_y=top_left_y,
        line_length=num_boxes_y * box_width,
        spacing=num_boxes_x * box_width,
        num_lines=2,
    )
    _add_horizontal_parallel_lines_to_image(
        image,
        start_x=top_left_x,
        start_y=top_left_y,
        line_length=num_boxes_x * box_width,
        spacing=num_boxes_y * box_width,
        num_lines=2,
    )


def add_grid_overlay_to_image(
    image: Image.Image,
    top_left_x: int,
    top_left_y: int,
    box_width: int,
    num_boxes_x: int,
    num_boxes_y: int,
):
    _add_vertical_parallel_lines_to_image(
        image,
        start_x=top_left_x + box_width,
        start_y=top_left_y,
        line_length=num_boxes_y * box_width,
        spacing=box_width,
        num_lines=num_boxes_x - 1,
    )
    _add_horizontal_parallel_lines_to_image(
        image,
        start_x=top_left_x,
        start_y=top_left_y + box_width,
        line_length=num_boxes_x * box_width,
        spacing=box_width,
        num_lines=num_boxes_y - 1,
    )


class SnapshotWithGrid(MJPG):
    top_left_x: Signal = Component(Signal)
    top_left_y: Signal = Component(Signal)
    box_width: Signal = Component(Signal)
    num_boxes_x: Signal = Component(Signal)
    num_boxes_y: Signal = Component(Signal)

    last_path_outer: Signal = Component(Signal)
    last_path_full_overlay: Signal = Component(Signal)

    def post_processing(self, image: Image.Image):
        top_left_x = self.top_left_x.get()
        top_left_y = self.top_left_y.get()
        box_width = self.box_width.get()
        num_boxes_x = self.num_boxes_x.get()
        num_boxes_y = self.num_boxes_y.get()
        filename_str = self.filename.get()
        directory_str = self.directory.get()
        add_grid_border_overlay_to_image(
            image, top_left_x, top_left_y, box_width, num_boxes_x, num_boxes_y
        )
        path = path_join(directory_str, f"{filename_str}_outer_overlay.png")
        self.last_path_outer.put(path)
        LOGGER.info(f"Saving {path}")
        image.save(path)
        add_grid_overlay_to_image(
            image, top_left_x, top_left_y, box_width, num_boxes_x, num_boxes_y
        )
        path = path_join(directory_str, f"{filename_str}_grid_overlay.png")
        self.last_path_full_overlay.put(path)
        LOGGER.info(f"Saving {path}")
        image.save(path)
