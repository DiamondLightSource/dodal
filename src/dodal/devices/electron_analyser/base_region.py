from pydantic import BaseModel


class BaseRegion(BaseModel):
    """
    Load in json file: BaseRegion.model_validate_json(json_str)
    get as json str: r.model_dump_json()
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
