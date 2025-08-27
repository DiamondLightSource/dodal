from typing import Generic

from pydantic import Field

from dodal.devices.electron_analyser.abstract.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.abstract.types import TLensMode, TPsuMode
from dodal.devices.electron_analyser.specs.enums import AcquisitionMode


class SpecsRegion(
    AbstractBaseRegion[AcquisitionMode, TLensMode, float],
    Generic[TLensMode, TPsuMode],
):
    """
    Represents a region configuration for a Specs electron analyser.

    This class extends `AbstractBaseRegion` and provides default values and additional
    fields specific to the Specs analyser region configuration.

    Type Parameters:
        TLensMode: The type representing the lens mode.
        TPsuMode: The type representing the PSU (Power Supply Unit) mode.

    Attributes:
        lens_mode (TLensMode): The lens mode for the region.
        pass_energy (float): The pass energy for the analyser (default: 5).
        acquisition_mode (AcquisitionMode): The acquisition mode (default: AcquisitionMode.FIXED_TRANSMISSION).
        low_energy (float): The starting energy for the region (default: 800, aliased as "start_energy").
        centre_energy (float): The centre energy for the region (default: 0).
        high_energy (float): The ending energy for the region (default: 850, aliased as "end_energy").
        acquire_time (float): The exposure time for acquisition (default: 1.0, aliased as "exposure_time").
        energy_step (float): The energy step size (default: 0.1, aliased as "step_energy").
        values (int): The number of values or points in the region (default: 1).
        psu_mode (TPsuMode): The PSU mode for the region.
        estimated_time_in_ms (float): The estimated acquisition time in milliseconds (default: 0).
    """

    # Override base class with defaults
    lens_mode: TLensMode
    pass_energy: float = 5
    acquisition_mode: AcquisitionMode = AcquisitionMode.FIXED_TRANSMISSION
    low_energy: float = Field(default=800, alias="start_energy")
    centre_energy: float = 0
    high_energy: float = Field(default=850, alias="end_energy")
    acquire_time: float = Field(default=1.0, alias="exposure_time")
    energy_step: float = Field(default=0.1, alias="step_energy")

    # Specific to this class
    values: int = 1
    psu_mode: TPsuMode
    estimated_time_in_ms: float = 0


class SpecsSequence(
    AbstractBaseSequence[SpecsRegion[TLensMode, TPsuMode]], Generic[TLensMode, TPsuMode]
):
    """
    A sequence container for SpecsRegion objects, parameterized by lens and PSU modes.

    This class manages a list of SpecsRegion instances, each configured with specific lens and PSU modes.
    It provides a structure for handling multiple regions in electron analyser specifications.

    Type Parameters:
        TLensMode: The type representing the lens mode.
        TPsuMode: The type representing the PSU mode.

    Attributes:
        regions (list[SpecsRegion[TLensMode, TPsuMode]]):
            A list of SpecsRegion objects, initialized as an empty list by default.
    """

    regions: list[SpecsRegion[TLensMode, TPsuMode]] = Field(default_factory=lambda: [])
