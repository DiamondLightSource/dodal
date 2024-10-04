import xml.etree.ElementTree as et
from dataclasses import dataclass


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

    def _read_zoom_params(self) -> dict:
        um_per_pix = {}
        for node in self.zoom_params:
            _zoom = str(_get_element_as_float(node, "level"))
            _um_pix_x = _get_element_as_float(node, "micronsPerXPixel")
            _um_pix_y = _get_element_as_float(node, "micronsPerYPixel")
            um_per_pix[_zoom] = {
                "microns_per_pixel_x": _um_pix_x,
                "microns_per_pixel_y": _um_pix_y,
            }
        return um_per_pix

    def _read_display_config(self) -> dict:
        crosshairs = {}
        for i in range(len(self.display_config)):
            if self.display_config[i].startswith("zoomLevel"):
                _zoom = self.display_config[i].split(" = ")[1].strip()
                _x = int(self.display_config[i + 1].split(" = ")[1])
                _y = int(self.display_config[i + 2].split(" = ")[1])
                crosshairs[_zoom] = {"crosshair_x": _x, "crosshair_y": _y}
        return crosshairs

    def get_parameters(self) -> dict[str, ZoomParams]:
        config = {}
        _um_xy = self._read_zoom_params()
        _bc_xy = self._read_display_config()
        for zoom_key in list(_bc_xy.keys()):
            config[zoom_key] = ZoomParams(
                microns_per_pixel_x=_um_xy["microns_per_pixel_x"],
                microns_per_pixel_y=_um_xy["microns_per_pixel_y"],
                crosshair_x=_bc_xy["crosshair_x"],
                crosshair_y=_bc_xy["crosshair_y"],
            )
        return config
