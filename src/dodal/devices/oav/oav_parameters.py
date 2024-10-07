import json
import xml.etree.ElementTree as et
from collections import ChainMap
from dataclasses import dataclass
from typing import Any
from xml.etree.ElementTree import Element

from dodal.devices.oav.oav_errors import (
    OAVError_BeamPositionNotFound,
    OAVError_ZoomLevelNotFound,
)
from dodal.log import LOGGER

# GDA currently assumes this aspect ratio for the OAV window size.
# For some beamline this doesn't affect anything as the actual OAV aspect ratio
# matches. Others need to take it into account to rescale the values stored in
# the configuration files.
DEFAULT_OAV_WINDOW = (1024, 768)

OAV_CONFIG_JSON = (
    "/dls_sw/i03/software/daq_configuration/json/OAVCentring_hyperion.json"
)


def _get_element_as_float(node: Element, element_name: str) -> float:
    element = node.find(element_name)
    assert element is not None, f"{element_name} not found in {node}"
    assert element.text
    return float(element.text)


class OAVParameters:
    """
    The parameters to set up the OAV depending on the context.
    """

    def __init__(
        self,
        context="loopCentring",
        oav_config_json=OAV_CONFIG_JSON,
    ):
        self.oav_config_json: str = oav_config_json
        self.context = context

        self.global_params, self.context_dicts = self.load_json(self.oav_config_json)
        self.active_params: ChainMap = ChainMap(
            self.context_dicts[self.context], self.global_params
        )
        self.update_self_from_current_context()

    @staticmethod
    def load_json(filename: str) -> tuple[dict[str, Any], dict[str, dict]]:
        """
        Loads the json from the specified file, and returns a dict with all the
        individual top-level k-v pairs, and one with all the subdicts.
        """
        with open(filename) as f:
            raw_params: dict[str, Any] = json.load(f)
        global_params = {
            k: raw_params.pop(k)
            for k, v in list(raw_params.items())
            if not isinstance(v, dict)
        }
        context_dicts = raw_params
        return global_params, context_dicts

    def update_context(self, context: str) -> None:
        self.active_params.maps.pop()
        self.active_params = self.active_params.new_child(self.context_dicts[context])

    def update_self_from_current_context(self) -> None:
        def update(name, param_type, default=None):
            param = self.active_params.get(name, default)
            try:
                param = param_type(param)
                return param
            except AssertionError as e:
                raise TypeError(
                    f"OAV param {name} from the OAV centring params json file has the "
                    f"wrong type, should be {param_type} but is {type(param)}."
                ) from e

        self.exposure: float = update("exposure", float)
        self.acquire_period: float = update("acqPeriod", float)
        self.gain: float = update("gain", float)
        self.canny_edge_upper_threshold: float = update(
            "CannyEdgeUpperThreshold", float
        )
        self.canny_edge_lower_threshold: float = update(
            "CannyEdgeLowerThreshold", float, default=5.0
        )
        self.minimum_height: int = update("minheight", int)
        self.zoom: float = update("zoom", float)
        self.preprocess: int = update(
            "preprocess", int
        )  # gets blur type, e.g. 8 = gaussianBlur, 9 = medianBlur
        self.preprocess_K_size: int = update(
            "preProcessKSize", int
        )  # length scale for blur preprocessing
        self.detection_script_filename: str = update("filename", str)
        self.close_ksize: int = update("close_ksize", int, default=11)
        self.min_callback_time: float = update("min_callback_time", float, default=0.08)
        self.direction: int = update("direction", int)
        self.max_tip_distance: float = update("max_tip_distance", float, default=300)

    def get_max_tip_distance_in_pixels(self, micronsPerPixel: float) -> float:
        """
        Get the maximum tip distance in pixels.
        """
        return self.max_tip_distance / micronsPerPixel


class OAVConfigParams:
    """
    The OAV parameters which may update depending on settings such as the zoom level.
    """

    def __init__(
        self,
        zoom_params_file,
        display_config,
    ):
        self.zoom_params_file: str = zoom_params_file
        self.display_config: str = display_config

    def update_on_zoom(self, value, xsize, ysize, *args, **kwargs):
        xsize, ysize = int(xsize), int(ysize)
        if isinstance(value, str) and value.endswith("x"):
            value = value.strip("x")
        zoom = float(value)
        self.load_microns_per_pixel(zoom, xsize, ysize)
        self.beam_centre_i, self.beam_centre_j = self.get_beam_position_from_zoom(
            zoom, xsize, ysize
        )

    def load_microns_per_pixel(self, zoom: float, xsize: int, ysize: int) -> None:
        """
        Loads the microns per x pixel and y pixel for a given zoom level. These are
        currently generated by GDA, though hyperion could generate them in future.
        """
        tree = et.parse(self.zoom_params_file)
        self.micronsPerXPixel = self.micronsPerYPixel = None
        root = tree.getroot()
        levels = root.findall(".//zoomLevel")
        for node in levels:
            if _get_element_as_float(node, "level") == zoom:
                self.micronsPerXPixel = (
                    _get_element_as_float(node, "micronsPerXPixel")
                    * DEFAULT_OAV_WINDOW[0]
                    / xsize
                )
                self.micronsPerYPixel = (
                    _get_element_as_float(node, "micronsPerYPixel")
                    * DEFAULT_OAV_WINDOW[1]
                    / ysize
                )
        if self.micronsPerXPixel is None or self.micronsPerYPixel is None:
            raise OAVError_ZoomLevelNotFound(
                f"""
                Could not find the micronsPer[X,Y]Pixel parameters in
                {self.zoom_params_file} for zoom level {zoom}.
                """
            )

    def get_beam_position_from_zoom(
        self, zoom: float, xsize: int, ysize: int
    ) -> tuple[int, int]:
        """
        Extracts the beam location in pixels `xCentre` `yCentre`, for a requested zoom \
        level. The beam location is manually inputted by the beamline operator on GDA \
        by clicking where on screen a scintillator lights up, and stored in the \
        display.configuration file.
        """
        crosshair_x_line = None
        crosshair_y_line = None
        with open(self.display_config) as f:
            file_lines = f.readlines()
            for i in range(len(file_lines)):
                if file_lines[i].startswith("zoomLevel = " + str(zoom)):
                    crosshair_x_line = file_lines[i + 1]
                    crosshair_y_line = file_lines[i + 2]
                    break

        if crosshair_x_line is None or crosshair_y_line is None:
            raise OAVError_BeamPositionNotFound(
                f"Could not extract beam position at zoom level {zoom}"
            )

        beam_centre_i = (
            int(crosshair_x_line.split(" = ")[1]) * xsize / DEFAULT_OAV_WINDOW[0]
        )
        beam_centre_j = (
            int(crosshair_y_line.split(" = ")[1]) * ysize / DEFAULT_OAV_WINDOW[1]
        )
        LOGGER.info(f"Beam centre: {beam_centre_i, beam_centre_j}")
        return int(beam_centre_i), int(beam_centre_j)

    def calculate_beam_distance(
        self, horizontal_pixels: int, vertical_pixels: int
    ) -> tuple[int, int]:
        """
        Calculates the distance between the beam centre and the given (horizontal, vertical).

        Args:
            horizontal_pixels (int): The x (camera coordinates) value in pixels.
            vertical_pixels (int): The y (camera coordinates) value in pixels.
        Returns:
            The distance between the beam centre and the (horizontal, vertical) point in pixels as a tuple
            (horizontal_distance, vertical_distance).
        """

        return (
            self.beam_centre_i - horizontal_pixels,
            self.beam_centre_j - vertical_pixels,
        )


@dataclass
class ZoomParams:
    microns_per_pixel_x: float
    microns_per_pixel_y: float
    crosshair_x: int
    crosshair_y: int


class OAVConfig:
    """ Read the OAV config files and return a dictionary of {'zoom_level': ZoomParams}\
    with information about microns per pixels and crosshairs.
    """

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
                microns_per_pixel_x=_um_xy[zoom_key]["microns_per_pixel_x"],
                microns_per_pixel_y=_um_xy[zoom_key]["microns_per_pixel_y"],
                crosshair_x=_bc_xy[zoom_key]["crosshair_x"],
                crosshair_y=_bc_xy[zoom_key]["crosshair_y"],
            )
        return config
