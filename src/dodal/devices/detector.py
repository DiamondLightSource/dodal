from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple

from dataclasses_json import config, dataclass_json

from dodal.devices.det_dim_constants import (
    EIGER2_X_16M_SIZE,
    DetectorSize,
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


@dataclass_json
@dataclass
class DetectorParams:
    current_energy: float
    exposure_time: float
    directory: str
    prefix: str
    run_number: int
    detector_distance: float
    omega_start: float
    omega_increment: float
    num_images_per_trigger: int
    num_triggers: int
    use_roi_mode: bool
    det_dist_to_beam_converter_path: str
    trigger_mode: TriggerMode = TriggerMode.SET_FRAMES

    detector_size_constants: DetectorSizeConstants = field(
        default_factory=lambda: EIGER2_X_16M_SIZE,
        metadata=config(
            encoder=lambda detector: detector.det_type_string,
            decoder=lambda det_type: constants_from_type(det_type),
        ),
    )

    # The following are optional from GDA as populated internally

    # Where the VDS start index should be in the Nexus file
    start_index: Optional[int] = 0
    nexus_file_run_number: Optional[int] = 0

    def __post_init__(self):
        if not self.directory.endswith("/"):
            self.directory += "/"

        self.beam_xy_converter = DetectorDistanceToBeamXYConverter(
            self.det_dist_to_beam_converter_path
        )

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
    def omega_end(self):
        return self.omega_start + self.num_triggers * self.omega_increment

    @property
    def full_filename(self):
        return f"{self.prefix}_{self.run_number}"

    @property
    def nexus_filename(self):
        return f"{self.prefix}_{self.nexus_file_run_number}"

    @property
    def full_number_of_images(self):
        return self.num_triggers * self.num_images_per_trigger
