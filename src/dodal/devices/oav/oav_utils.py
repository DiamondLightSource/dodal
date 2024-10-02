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
    def __init__(self, zoom_params_file: str, display_config: str):
        self.zoom_params_file = zoom_params_file
        self.display_config = display_config

    def _read_zoom_params(self):
        pass

    def _read_display_config(self, zoom: str):
        crosshair_x_line = None
        crosshair_y_line = None
        with open(self.display_config) as f:
            file_lines = f.readlines()
            for i in range(len(file_lines)):
                if file_lines[i].startswith("zoomLevel = " + zoom):
                    crosshair_x_line = file_lines[i + 1]
                    crosshair_y_line = file_lines[i + 2]
                    break

        if crosshair_x_line is None or crosshair_y_line is None:
            raise OAVError_BeamPositionNotFound(
                f"Could not extract beam position at zoom level {zoom}"
            )
        return crosshair_x_line.split(" = ")[1], crosshair_y_line.split(" = ")[1]

    def get_parameters(self, allowed_zoom_levels: list[str]) -> dict[str, ZoomParams]:
        pass


# NOTE: Beware of the zoom which could have an x or not, but in the files never does.
# Might want to pass the available zoom levels just to create the correct dict.
