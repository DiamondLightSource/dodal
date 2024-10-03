import xml.etree.ElementTree as et
from dataclasses import dataclass

from dodal.devices.oav.oav_errors import (
    OAVError_BeamPositionNotFound,
    OAVError_ZoomLevelNotFound,
)


@dataclass
class ZoomParams:
    microns_per_pixel_x: float
    microns_per_pixel_y: float
    crosshair_x: int
    crosshair_y: int


def _get_element_as_float(node: et.Element, element_name: str) -> float:
    element = node.find(element_name)
    assert element is not None, f"{element_name} not found in {node}"
    assert element.text
    return float(element.text)


def _get_correct_zoom_string(zoom: str) -> str:
    if zoom.endswith("x"):
        zoom = zoom.strip("x")
    return zoom


# Probably needs something similar to OAVCOnfigParams but that just read the files,
# fills a dictionary {"zoom_level_name": OAVParams} and returns it
class OAVConfig:
    def __init__(self, zoom_params_file: str, display_config_file: str):
        self.zoom_params = self._get_zoom_params(zoom_params_file)
        self.display_config = self._get_display_config(display_config_file)

    def _get_display_config(self, display_config_file: str):
        with open(display_config_file) as f:
            file_lines = f.readlines()
        return file_lines

    def _get_zoom_params(self, zoom_params_file: str):
        tree = et.parse(zoom_params_file)
        root = tree.getroot()
        return root.findall(".//zoomLevel")

    def _read_zoom_params(self, zoom: str) -> tuple[float, float]:
        zoom = _get_correct_zoom_string(zoom)
        um_per_x_pix = None
        um_per_y_pix = None
        for node in self.zoom_params:
            if _get_element_as_float(node, "level") == zoom:
                um_per_x_pix = _get_element_as_float(node, "micronsPerXPixel")
                um_per_y_pix = _get_element_as_float(node, "micronsPerYPixel")
        if not um_per_y_pix or not um_per_x_pix:
            raise OAVError_ZoomLevelNotFound(
                f"""
                Could not find the micronsPer[X,Y]Pixel parameters in
                for zoom level {zoom}.
                """
            )
        return um_per_x_pix, um_per_y_pix

    def _read_display_config(self, zoom: str) -> tuple[int, int]:
        zoom = _get_correct_zoom_string(zoom)
        crosshair_x_line = None
        crosshair_y_line = None
        for i in range(len(self.display_config)):
            if self.display_config[i].startswith("zoomLevel = " + zoom):
                crosshair_x_line = self.display_config[i + 1]
                crosshair_y_line = self.display_config[i + 2]
                break

        if crosshair_x_line is None or crosshair_y_line is None:
            raise OAVError_BeamPositionNotFound(
                f"Could not extract beam position at zoom level {zoom}"
            )
        return int(crosshair_x_line.split(" = ")[1]), int(
            crosshair_y_line.split(" = ")[1]
        )

    def get_parameters(self, allowed_zoom_levels: list[str]) -> dict[str, ZoomParams]:
        config = {}
        for zoom in allowed_zoom_levels:
            _um_xy = self._read_zoom_params(zoom)
            _bc_xy = self._read_display_config(zoom)
            config[zoom] = ZoomParams(
                microns_per_pixel_x=_um_xy[0],
                microns_per_pixel_y=_um_xy[1],
                crosshair_x=_bc_xy[0],
                crosshair_y=_bc_xy[1],
            )
        return config
