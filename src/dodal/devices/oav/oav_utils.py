import xml.etree.ElementTree as et
from dataclasses import dataclass

from dodal.devices.oav.oav_errors import OAVError_BeamPositionNotFound

DEFAULT_OAV_WINDOW = (1024, 768)


@dataclass
class ZoomParams:
    position: float
    microns_per_pixel_x: float
    microns_per_pixel_y: float
    crosshair_x: int
    crosshair_y: int


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

    def _read_zoom_params(self):
        pass

    def _read_display_config(self, zoom: str):
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
        return crosshair_x_line.split(" = ")[1], crosshair_y_line.split(" = ")[1]

    def get_parameters(self, allowed_zoom_levels: list[str]) -> dict[str, ZoomParams]:
        config = {zoom: ZoomParams for zoom in allowed_zoom_levels}
        print(config)
        # return config


# NOTE: Beware of the zoom which could have an x or not, but in the files never does.
# Might want to pass the available zoom levels just to create the correct dict.
