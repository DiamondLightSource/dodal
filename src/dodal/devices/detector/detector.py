from enum import Enum, auto
from typing import Any, Tuple

from pydantic import BaseModel, root_validator, validator

from dodal.devices.detector.det_dim_constants import (
    EIGER2_X_16M_SIZE,
    DetectorSize,
    DetectorSizeConstants,
    constants_from_type,
)
from dodal.devices.detector.det_dist_to_beam_converter import (
    Axis,
    DetectorDistanceToBeamXYConverter,
)
from dodal.utils import get_run_number


class TriggerMode(Enum):
    """In set frames the number of frames is known at arm time. In free run they are
    not known until the detector is unstaged."""

    SET_FRAMES = auto()
    FREE_RUN = auto()


class DetectorParams(BaseModel):
    """Holds parameters for the detector. Provides access to a list of Dectris detector
    sizes and a converter for distance to beam centre."""

    expected_energy_ev: float | None = None
    exposure_time: float
    directory: str
    prefix: str
    detector_distance: float
    omega_start: float
    omega_increment: float
    num_images_per_trigger: int
    num_triggers: int
    use_roi_mode: bool
    det_dist_to_beam_converter_path: str
    trigger_mode: TriggerMode = TriggerMode.SET_FRAMES
    detector_size_constants: DetectorSizeConstants = EIGER2_X_16M_SIZE
    beam_xy_converter: DetectorDistanceToBeamXYConverter
    run_number: int
    enable_dev_shm: bool = (
        False  # Remove in https://github.com/DiamondLightSource/hyperion/issues/1395
    )

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            DetectorDistanceToBeamXYConverter: lambda _: None,
            DetectorSizeConstants: lambda d: d.det_type_string,
        }

    @root_validator(pre=True, skip_on_failure=True)  # type: ignore # should be replaced with model_validator once move to pydantic 2 is complete
    def create_beamxy_and_runnumber(cls, values: dict[str, Any]) -> dict[str, Any]:
        values["beam_xy_converter"] = DetectorDistanceToBeamXYConverter(
            values["det_dist_to_beam_converter_path"]
        )
        if values.get("run_number") is None:
            values["run_number"] = get_run_number(values["directory"])
        return values

    @validator("detector_size_constants", pre=True)
    def _parse_detector_size_constants(
        cls, det_type: str, values: dict[str, Any]
    ) -> DetectorSizeConstants:
        return constants_from_type(det_type)

    @validator("directory", pre=True)
    def _parse_directory(cls, directory: str, values: dict[str, Any]) -> str:
        if not directory.endswith("/"):
            directory += "/"
        return directory

    def get_beam_position_mm(self, detector_distance: float) -> Tuple[float, float]:
        x_beam_mm = self.beam_xy_converter.get_beam_xy_from_det_dist(
            detector_distance, Axis.X_AXIS
        )
        y_beam_mm = self.beam_xy_converter.get_beam_xy_from_det_dist(
            detector_distance, Axis.Y_AXIS
        )

        full_size_mm = self.detector_size_constants.det_dimension
        roi_size_mm = (
            self.detector_size_constants.roi_dimension
            if self.use_roi_mode
            else full_size_mm
        )

        offset_x = (full_size_mm.width - roi_size_mm.width) / 2.0
        offset_y = (full_size_mm.height - roi_size_mm.height) / 2.0

        return x_beam_mm - offset_x, y_beam_mm - offset_y

    def get_detector_size_pizels(self) -> DetectorSize:
        full_size = self.detector_size_constants.det_size_pixels
        roi_size = self.detector_size_constants.roi_size_pixels
        return roi_size if self.use_roi_mode else full_size

    def get_beam_position_pixels(self, detector_distance: float) -> Tuple[float, float]:
        full_size_pixels = self.detector_size_constants.det_size_pixels
        roi_size_pixels = self.get_detector_size_pizels()

        x_beam_pixels = self.beam_xy_converter.get_beam_x_pixels(
            detector_distance,
            full_size_pixels.width,
            self.detector_size_constants.det_dimension.width,
        )
        y_beam_pixels = self.beam_xy_converter.get_beam_y_pixels(
            detector_distance,
            full_size_pixels.height,
            self.detector_size_constants.det_dimension.height,
        )

        offset_x = (full_size_pixels.width - roi_size_pixels.width) / 2.0
        offset_y = (full_size_pixels.height - roi_size_pixels.height) / 2.0

        return x_beam_pixels - offset_x, y_beam_pixels - offset_y

    @property
    def full_filename(self):
        return f"{self.prefix}_{self.run_number}"

    @property
    def full_number_of_images(self):
        return self.num_triggers * self.num_images_per_trigger
