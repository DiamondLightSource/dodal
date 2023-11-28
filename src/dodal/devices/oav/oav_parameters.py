import json
from collections import ChainMap
from typing import Any

OAV_CONFIG_JSON = (
    "/dls_sw/i03/software/daq_configuration/json/OAVCentring_hyperion.json"
)


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
            except AssertionError:
                raise TypeError(
                    f"OAV param {name} from the OAV centring params json file has the "
                    f"wrong type, should be {param_type} but is {type(param)}."
                )

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
