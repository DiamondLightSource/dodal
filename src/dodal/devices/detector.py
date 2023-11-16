from enum import Enum, auto
from typing import Any, Optional, Tuple

from pydantic import BaseModel, validator

from dodal.devices.det_dim_constants import (
    EIGER2_X_16M_SIZE,
    DetectorSize_pixels,
    DetectorSizeConstants,
    constants_from_type,
)
from dodal.devices.det_dist_to_beam_converter import (
    Axis,
    DetectorDistanceToBeamXYConverter,
)


class TriggerMode(Enum):
    """In set frames the number of frames is known at arm time. In free run they are
    not known until the detector is unstaged."""

    SET_FRAMES = auto()
    FREE_RUN = auto()


class DetectorParams(BaseModel):
    """Holds parameters for the detector. Provides access to a list of Dectris detector
    sizes and a converter for distance to beam centre."""

    energy_ev: float
    exposure_time_s: float
    directory: str
    prefix: str
    run_number: int
    detector_distance_mm: float
    omega_start_deg: float
    omega_increment_deg: float
    num_images_per_trigger: int = 1
    num_triggers: int = 1
    use_roi_mode: bool
    det_dist_to_beam_converter_path: str
    trigger_mode: TriggerMode = TriggerMode.SET_FRAMES
    detector_size_constants: DetectorSizeConstants = EIGER2_X_16M_SIZE
    beam_xy_converter: DetectorDistanceToBeamXYConverter

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            DetectorDistanceToBeamXYConverter: lambda _: None,
            DetectorSizeConstants: lambda d: d.det_type_string,
        }

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

    @validator("trigger_mode", pre=True)
    def _parse_trigger_mode(cls, trigger_mode: str | int | TriggerMode):
        if isinstance(trigger_mode, TriggerMode):
            return trigger_mode
        if isinstance(trigger_mode, str):
            return TriggerMode[trigger_mode]
        else:
            return TriggerMode(trigger_mode)

    @validator("beam_xy_converter", always=True)
    def _parse_beam_xy_converter(
        cls,
        beam_xy_converter: DetectorDistanceToBeamXYConverter,
        values: dict[str, Any],
    ) -> DetectorDistanceToBeamXYConverter:
        return DetectorDistanceToBeamXYConverter(
            values["det_dist_to_beam_converter_path"]
        )

    # The following are optional from GDA as populated internally
    # Where the VDS start index should be in the Nexus file
    start_index: Optional[int] = 0
    nexus_file_run_number: Optional[int] = 0

    def __post_init__(self):
        self.beam_xy_converter = DetectorDistanceToBeamXYConverter(
            self.det_dist_to_beam_converter_path
        )

    def get_beam_position_mm(self, detector_distance_mm: float) -> Tuple[float, float]:
        x_beam_mm = self.beam_xy_converter.get_beam_xy_from_det_dist(
            detector_distance_mm, Axis.X_AXIS
        )
        y_beam_mm = self.beam_xy_converter.get_beam_xy_from_det_dist(
            detector_distance_mm, Axis.Y_AXIS
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

    def get_detector_size_pixels(self) -> DetectorSize_pixels:
        full_size = self.detector_size_constants.det_size_pixels
        roi_size = self.detector_size_constants.roi_size_pixels
        return roi_size if self.use_roi_mode else full_size

    def get_beam_position_pixels(
        self, detector_distance_mm: float
    ) -> Tuple[float, float]:
        full_size_pixels = self.detector_size_constants.det_size_pixels
        roi_size_pixels = self.get_detector_size_pixels()

        x_beam_pixels = self.beam_xy_converter.get_beam_x_pixels(
            detector_distance_mm,
            full_size_pixels.width,
            self.detector_size_constants.det_dimension.width,
        )
        y_beam_pixels = self.beam_xy_converter.get_beam_y_pixels(
            detector_distance_mm,
            full_size_pixels.height,
            self.detector_size_constants.det_dimension.height,
        )

        offset_x = (full_size_pixels.width - roi_size_pixels.width) / 2.0
        offset_y = (full_size_pixels.height - roi_size_pixels.height) / 2.0

        return x_beam_pixels - offset_x, y_beam_pixels - offset_y

    @property
    def omega_end(self):
        return self.omega_start_deg + self.num_triggers * self.omega_increment_deg

    @property
    def full_filename(self):
        return f"{self.prefix}_{self.run_number}"

    @property
    def nexus_filename(self):
        return f"{self.prefix}_{self.nexus_file_run_number}"

    @property
    def full_number_of_images(self):
        return self.num_triggers * self.num_images_per_trigger
