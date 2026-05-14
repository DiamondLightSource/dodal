from os.path import basename, split
from typing import Generic, Self

import xmltodict
from pydantic import Field, field_validator

from dodal.devices.beamlines.i05.enums import LensMode, PassEnergy
from dodal.devices.electron_analyser.base.base_region import (
    BaseRegion,
    BaseSequence,
    TLensMode,
    TPassEnergy,
)
from dodal.devices.electron_analyser.mbs.mbs_enums import AcquisitionMode


class MbsRegion(
    BaseRegion[AcquisitionMode, TLensMode, TPassEnergy],
    Generic[TLensMode, TPassEnergy],
):
    # Override base class with defaults
    lens_mode: TLensMode
    pass_energy: TPassEnergy
    acquisition_mode: AcquisitionMode = AcquisitionMode.FIXED
    low_energy: float = Field(default=800, alias="start_energy")
    high_energy: float = Field(default=850, alias="end_energy")
    centre_energy: float = Field(
        default_factory=lambda data: (data["high_energy"] + data["low_energy"]) / 2
    )
    acquire_time: float = Field(default=1.0, alias="time_per_step")
    energy_step: float = Field(default=0.1, alias="step_energy")
    # Default is True as mbs ususally only uses one region.
    enabled: bool = True

    # Specific to this class
    deflector_x: float = 0

    @staticmethod
    def convert_pass_energy_to_analyser_string(pass_energy) -> str:
        return f"PE{int(pass_energy):03d}"

    @field_validator("pass_energy", mode="before")
    @classmethod
    def convert_pass_energy(cls, value):
        return cls.convert_pass_energy_to_analyser_string(value)

    @classmethod
    def from_xml(cls, file: str) -> Self:
        path, extension = split(file)
        name = basename(path)
        with open(file) as f:
            data = xmltodict.parse(f.read())
        region = cls.model_validate(data["ARPESScanBean"])
        region.name = name
        return region


class MbsSequence(
    BaseSequence[MbsRegion[TLensMode, TPassEnergy]], Generic[TLensMode, TPassEnergy]
):
    @classmethod
    def from_xml(cls, files: list[str]) -> Self:
        regions = []
        annotation = cls.model_fields["regions"].annotation
        if annotation is None:
            raise ValueError("Please provide the LensMode and PassEnergy types.")

        # Must find the region type annotation because reconstructing the generic
        # manually doing MbsRegion[TLensMode, TPassEnergy].from_xml(file) will not work.
        region_type = annotation.__args__[0]
        for file in files:
            regions.append(region_type.from_xml(file))
        return cls.model_validate({"regions": regions})


print(
    MbsRegion[LensMode, PassEnergy].from_xml(
        "/workspaces/dodal/tests/devices/electron_analyser/test_data/mbs_region1.arpes"
    )
)

print(
    MbsSequence[LensMode, PassEnergy].from_xml(
        [
            "/workspaces/dodal/tests/devices/electron_analyser/test_data/mbs_region1.arpes"
        ],
    )
)
