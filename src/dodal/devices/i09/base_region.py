from dataclasses import dataclass, field

alias_region_fields = {
    "startEnergy": "lowEnergy",
    "endEnergy": "highEnergy",
    "exposureTime": "stepTime",
    "stepEnergy": "energyStep",
}


def alias_fields(kwargs) -> dict:
    return {
        alias_region_fields[arg] if arg in alias_region_fields else arg: value
        for arg, value in kwargs.items()
    }


@dataclass(kw_only=True, match_args=False)
class AbstractBaseRegion:
    # Defaults are defined in AbstractBaseRegion.get_default_values() which should be overwritten
    name: str = "New_region"
    enabled: bool = False
    slices: int = 1
    iterations: int = 1
    lensMode: str = ""
    lowEnergy: float = -1
    highEnergy: float = -1
    stepTime: float = -1
    energyStep: float = -1


class SPECSRegion(AbstractBaseRegion):
    bindingEnergy: bool = field(default=False)
    passEnergy: float = 1
    value: float = field(default=1)
    centreEnergy: float = field(default=0)
    psuMode: str = field(default="1.5keV")
    acquisitionMode: str = ""
