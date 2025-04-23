from enum import Enum, auto
from functools import cached_property
from pathlib import Path

from pydantic import BaseModel, Field, field_serializer, field_validator

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

    # https://github.com/pydantic/pydantic/issues/8379
    # Must use model_dump(by_alias=True) if serialising!

    expected_energy_ev: float | None = None
    exposure_time_s: float
    directory: str  # : Path https://github.com/DiamondLightSource/dodal/issues/774
    prefix: str
    detector_distance: float
    omega_start: float
    omega_increment: float
    num_images_per_trigger: int
    num_triggers: int
    use_roi_mode: bool
    det_dist_to_beam_converter_path: str
    override_run_number: int | None = Field(default=None, alias="run_number")
    trigger_mode: TriggerMode = TriggerMode.SET_FRAMES
    detector_size_constants: DetectorSizeConstants = EIGER2_X_16M_SIZE
    enable_dev_shm: bool = (
        False  # Remove in https://github.com/DiamondLightSource/hyperion/issues/1395
    )

    @cached_property
    def beam_xy_converter(self) -> DetectorDistanceToBeamXYConverter:
        return DetectorDistanceToBeamXYConverter(self.det_dist_to_beam_converter_path)

    @property
    def run_number(self) -> int:
        return (
            get_run_number(self.directory, self.prefix)
            if self.override_run_number is None
            else self.override_run_number
        )

    @field_serializer("detector_size_constants")
    def serialize_detector_size_constants(self, size: DetectorSizeConstants):
        return size.det_type_string

    @field_validator("detector_size_constants", mode="before")
    @classmethod
    def _parse_detector_size_constants(cls, det_type: str) -> DetectorSizeConstants:
        return (
            det_type
            if isinstance(det_type, DetectorSizeConstants)
            else constants_from_type(det_type)
        )

    @field_validator("directory", mode="before")
    @classmethod
    def _parse_directory(cls, directory: str | Path) -> str:
        path = Path(directory)
        assert path.is_dir()
        return f"{path}/"

    def get_beam_position_mm(self, detector_distance: float) -> tuple[float, float]:
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

    def get_beam_position_pixels(self, detector_distance: float) -> tuple[float, float]:
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
