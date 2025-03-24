from abc import abstractmethod
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, model_validator


class EnergyMode(str, Enum):
    KINETIC = "Kinetic"
    BINDING = "Binding"


class AbstractBaseRegion(BaseModel):
    """
    Generic region model that holds the data. Specialised region models should inherit
    this to extend functionality.
    """

    name: str = "New_region"
    enabled: bool = False
    slices: int = 1
    iterations: int = 1
    # These ones we need subclasses to provide default values
    lensMode: str
    passEnergy: int | float
    acquisitionMode: str
    lowEnergy: float
    highEnergy: float
    stepTime: float
    energyStep: float  # in eV
    energyMode: EnergyMode = EnergyMode.KINETIC

    @abstractmethod
    def get_energy_step_eV(self) -> float:
        pass

    def is_binding_energy(self) -> bool:
        return self.energyMode == EnergyMode.BINDING

    def is_kinetic_energy(self) -> bool:
        return self.energyMode == EnergyMode.KINETIC

    def to_kinetic_energy(self, value: float, excitation_energy: float) -> float:
        return value if self.is_binding_energy() else excitation_energy - value

    @model_validator(mode="before")
    @classmethod
    def check_energy_mode(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # convert bindingEnergy to energyMode to make base region more generic
            if "bindingEnergy" in data:
                is_binding_energy = data["bindingEnergy"]
                del data["bindingEnergy"]
                data["energyMode"] = (
                    EnergyMode.BINDING if is_binding_energy else EnergyMode.KINETIC
                )
        return data


TAbstractBaseRegion = TypeVar("TAbstractBaseRegion", bound=AbstractBaseRegion)


class BaseSequence(BaseModel, Generic[TAbstractBaseRegion]):
    """
    Generic sequence model that holds the list of region data. Specialised sequence models
    should inherit this to extend functionality.
    """

    regions: list[TAbstractBaseRegion] = Field(default_factory=lambda: [])

    def get_enabled_regions(self) -> list[TAbstractBaseRegion]:
        return [r for r in self.regions if r.enabled]

    def get_region_names(self) -> list[str]:
        return [r.name for r in self.regions]

    def get_enabled_region_names(self) -> list[str]:
        return [r.name for r in self.get_enabled_regions()]

    def get_region_by_name(self, name: str) -> TAbstractBaseRegion | None:
        return next((region for region in self.regions if region.name == name), None)
