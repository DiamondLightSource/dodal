import uuid
from typing import Generic

from pydantic import Field, field_validator

from dodal.devices.electron_analyser.abstract.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.abstract.types import (
    TLensMode,
    TPassEnergyEnum,
    TPsuMode,
)
from dodal.devices.electron_analyser.vgscienta.enums import (
    AcquisitionMode,
    DetectorMode,
)


class VGScientaRegion(
    AbstractBaseRegion[AcquisitionMode, TLensMode, TPassEnergyEnum],
    Generic[TLensMode, TPassEnergyEnum],
):
    """
    Represents a region configuration for a VG Scienta electron analyser.

    This class extends the abstract base region and provides additional fields and defaults
    specific to the VG Scienta analyser, including lens mode, pass energy, acquisition mode,
    energy range, acquisition timing, and detector configuration.

    Attributes:
        lens_mode (TLensMode): The lens mode used for the region.
        pass_energy (TPassEnergyEnum): The pass energy setting for the region.
        acquisition_mode (AcquisitionMode): The acquisition mode (default: SWEPT).
        low_energy (float): The lower bound of the energy window (default: 8.0).
        centre_energy (float): The center energy value, aliased as "fix_energy" (default: 9).
        high_energy (float): The upper bound of the energy window (default: 10.0).
        acquire_time (float): The acquisition time per step, aliased as "step_time" (default: 1.0).
        energy_step (float): The energy step size (default: 200.0).
        id (str): Unique identifier for the region, aliased as "region_id".
        total_steps (float): Total number of steps in the region (default: 13.0).
        total_time (float): Total acquisition time for the region (default: 13.0).
        min_x (int): Minimum X channel, aliased as "first_x_channel" (default: 1).
        sensor_max_size_x (int): Maximum X channel, aliased as "last_x_channel" (default: 1000).
        min_y (int): Minimum Y channel, aliased as "first_y_channel" (default: 101).
        sensor_max_size_y (int): Maximum Y channel, aliased as "last_y_channel" (default: 800).
        detector_mode (DetectorMode): Detector mode (default: ADC).

    Properties:
        size_x (int): The number of X channels in the region.
        size_y (int): The number of Y channels in the region.

    Methods:
        validate_pass_energy(val): Validates and converts the pass energy value to a string
            to ensure correct enum casting.
    """

    # Override defaults of base region class
    lens_mode: TLensMode
    pass_energy: TPassEnergyEnum
    acquisition_mode: AcquisitionMode = AcquisitionMode.SWEPT
    low_energy: float = 8.0
    centre_energy: float = Field(alias="fix_energy", default=9)
    high_energy: float = 10.0
    acquire_time: float = Field(default=1.0, alias="step_time")
    energy_step: float = Field(default=200.0)
    # Specific to this class
    id: str = Field(default=str(uuid.uuid4()), alias="region_id")
    total_steps: float = 13.0
    total_time: float = 13.0
    min_x: int = Field(alias="first_x_channel", default=1)
    sensor_max_size_x: int = Field(alias="last_x_channel", default=1000)
    min_y: int = Field(alias="first_y_channel", default=101)
    sensor_max_size_y: int = Field(alias="last_y_channel", default=800)
    detector_mode: DetectorMode = DetectorMode.ADC

    @property
    def size_x(self) -> int:
        return self.sensor_max_size_x - self.min_x + 1

    @property
    def size_y(self) -> int:
        return self.sensor_max_size_y - self.min_y + 1

    @field_validator("pass_energy", mode="before")
    @classmethod
    def validate_pass_energy(cls, val):
        # This is needed because if the value is a number, it can't be casted to the
        # enum correctly.
        return str(val)


class VGScientaSequence(
    AbstractBaseSequence[VGScientaRegion[TLensMode, TPassEnergyEnum]],
    Generic[TLensMode, TPsuMode, TPassEnergyEnum],
):
    """
    Represents a sequence of VG Scienta regions for an electron analyser.

    This class is a generic container for managing a sequence of measurement regions,
    each defined by lens mode and pass energy settings. It also includes a power supply
    unit (PSU) mode associated with the sequence.

    Type Parameters:
        TLensMode: The type representing the lens mode.
        TPsuMode: The type representing the PSU mode.
        TPassEnergyEnum: The type representing the pass energy enumeration.

    Attributes:
        psu_mode (TPsuMode): The PSU mode for the sequence, mapped from the 'element_set' alias.
        regions (list[VGScientaRegion[TLensMode, TPassEnergyEnum]]):
            A list of VGScientaRegion objects, each specifying a region with its own lens mode and pass energy.
    """

    psu_mode: TPsuMode = Field(alias="element_set")
    regions: list[VGScientaRegion[TLensMode, TPassEnergyEnum]] = Field(
        default_factory=lambda: []
    )
