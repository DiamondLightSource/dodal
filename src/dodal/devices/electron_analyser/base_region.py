from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class BaseRegion(BaseModel):
    """
    Generic region model that holds the region data. Specialised region models
    should inherit this to extend functionality.
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
    energyStep: float


TBaseRegion = TypeVar("TBaseRegion", bound=BaseRegion)


class BaseSequence(BaseModel, Generic[TBaseRegion]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    regions: list[TBaseRegion] = Field(default_factory=lambda: [])

    def get_enabled_regions(self) -> list[BaseRegion]:
        return [r for r in self.regions if r.enabled]

    def get_region_names(self) -> list[str]:
        return [r.name for r in self.regions]
