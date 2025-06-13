from os.path import join as path_join

from ophyd_async.core import soft_signal_rw
from PIL.Image import Image

from dodal.devices.areadetector.plugins.MJPG import IMG_FORMAT, MJPG, asyncio_save_image
from dodal.devices.oav.snapshots.grid_overlay import (
    add_grid_border_overlay_to_image,
    add_grid_overlay_to_image,
)
from dodal.log import LOGGER


class SnapshotWithGrid(MJPG):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.top_left_x = soft_signal_rw(float)
            self.top_left_y = soft_signal_rw(float)
            self.box_width = soft_signal_rw(float)
            self.num_boxes_x = soft_signal_rw(int)
            self.num_boxes_y = soft_signal_rw(int)

            self.last_path_outer = soft_signal_rw(str)
            self.last_path_full_overlay = soft_signal_rw(str)

        super().__init__(prefix, name)

    async def post_processing(self, image: Image):
        # Save an unmodified image with no suffix
        await self._save_image(image)

        top_left_x = await self.top_left_x.get_value()
        top_left_y = await self.top_left_y.get_value()
        box_width = await self.box_width.get_value()
        num_boxes_x = await self.num_boxes_x.get_value()
        num_boxes_y = await self.num_boxes_y.get_value()
        filename_str = await self.filename.get_value()
        assert isinstance(filename_str, str)
        directory_str = await self.directory.get_value()
        assert isinstance(directory_str, str)

        add_grid_border_overlay_to_image(
            image, int(top_left_x), int(top_left_y), box_width, num_boxes_x, num_boxes_y
        )

        path = path_join(directory_str, f"{filename_str}_outer_overlay.{IMG_FORMAT}")
        await self.last_path_outer.set(path, wait=True)
        LOGGER.info(f"Saving grid outer edge at {path}")
        await asyncio_save_image(image, path)

        add_grid_overlay_to_image(
            image, int(top_left_x), int(top_left_y), box_width, num_boxes_x, num_boxes_y
        )

        path = path_join(directory_str, f"{filename_str}_grid_overlay.{IMG_FORMAT}")
        await self.last_path_full_overlay.set(path, wait=True)
        LOGGER.info(f"Saving full grid overlay at {path}")
        await asyncio_save_image(image, path)
