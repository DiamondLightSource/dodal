import re
from abc import ABC
from collections.abc import Callable
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, model_validator

from dodal.devices.electron_analyser.abstract.types import (
    TAcquisitionMode,
    TLensMode,
    TPassEnergy,
)
from dodal.devices.electron_analyser.enums import EnergyMode, SelectedSource
from dodal.devices.electron_analyser.util import to_binding_energy, to_kinetic_energy


def java_to_python_case(java_str: str) -> str:
    """
    Convert a camelCase Java-style string to a snake_case Python-style string.

    :param java_str: The Java-style camelCase string.
    :return: The Python-style snake_case string.
    """
    new_value = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", java_str)
    new_value = re.sub("([a-z0-9])([A-Z])", r"\1_\2", new_value).lower()
    return new_value


def switch_case_validation(data: dict, f: Callable[[str], str]) -> dict:
    return {f(key): value for key, value in data.items()}


class JavaToPythonModel(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def before_validation(cls, data: dict) -> dict:
        data = switch_case_validation(data, java_to_python_case)
        return data


def energy_mode_validation(data: dict) -> dict:
    # Convert binding_energy to energy_mode to make base region more generic
    if "binding_energy" in data:
        is_binding_energy = data["binding_energy"]
        del data["binding_energy"]
        data["energy_mode"] = (
            EnergyMode.BINDING if is_binding_energy else EnergyMode.KINETIC
        )
    return data


class AbstractBaseRegion(
    ABC,
    JavaToPythonModel,
    Generic[TAcquisitionMode, TLensMode, TPassEnergy],
):
    """
    Generic region model that holds the data. Specialised region models should inherit
    this to extend functionality. All energy units are assumed to be in eV.
    """

    name: str = "New_region"
    enabled: bool = False
    slices: int = 1
    iterations: int = 1
    excitation_energy_source: SelectedSource = SelectedSource.SOURCE1
    # These ones we need subclasses to provide default values
    lens_mode: TLensMode
    pass_energy: TPassEnergy
    acquisition_mode: TAcquisitionMode
    low_energy: float
    centre_energy: float
    high_energy: float
    acquire_time: float
    energy_step: float  # in eV
    energy_mode: EnergyMode = EnergyMode.KINETIC

    def is_binding_energy(self) -> bool:
        """
        Returns true if the energy_mode is binding.
        """
        return self.energy_mode == EnergyMode.BINDING

    def is_kinetic_energy(self) -> bool:
        """
        Returns true if the energy_mode is kinetic.
        """
        return self.energy_mode == EnergyMode.KINETIC

    def switch_energy_mode(
        self, energy_mode: EnergyMode, excitation_energy: float
    ) -> None:
        """
        Switch region to new energy mode: Kinetic or Binding. Updates the low_energy,
        centre_energy, high_energy, and energy_mode, only if it switches to a new one.

        Parameters:
            energy_mode: mode you want to switch the region to.
            excitation_energy: the energy to calculate the new values of low_energy,
                               centre_energy, and high_energy.
        """
        conv = (
            to_binding_energy
            if energy_mode == EnergyMode.BINDING
            else to_kinetic_energy
        )
        self.low_energy = conv(self.low_energy, self.energy_mode, excitation_energy)
        self.centre_energy = conv(
            self.centre_energy, self.energy_mode, excitation_energy
        )
        self.high_energy = conv(self.high_energy, self.energy_mode, excitation_energy)
        self.energy_mode = energy_mode

    @model_validator(mode="before")
    @classmethod
    def before_validation(cls, data: dict) -> dict:
        data = switch_case_validation(data, java_to_python_case)
        return energy_mode_validation(data)


TAbstractBaseRegion = TypeVar("TAbstractBaseRegion", bound=AbstractBaseRegion)


class AbstractBaseSequence(
    ABC,
    JavaToPythonModel,
    Generic[TAbstractBaseRegion],
):
    """
    Generic sequence model that holds the list of region data. Specialised sequence
    models should inherit this to extend functionality and define type of region to
    hold.
    """

    version: float = 0.1  # If file format changes within prod, increment this number!
    regions: list[TAbstractBaseRegion] = Field(default_factory=lambda: [])

    def get_enabled_regions(self) -> list[TAbstractBaseRegion]:
        return [r for r in self.regions if r.enabled]

    def get_region_names(self) -> list[str]:
        return [r.name for r in self.regions]

    def get_enabled_region_names(self) -> list[str]:
        return [r.name for r in self.get_enabled_regions()]

    def get_region_by_name(self, name: str) -> TAbstractBaseRegion | None:
        return next((region for region in self.regions if region.name == name), None)


TAbstractBaseSequence = TypeVar("TAbstractBaseSequence", bound=AbstractBaseSequence)
