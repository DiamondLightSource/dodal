from ophyd_async.core import StrictEnum


class LensMode(StrictEnum):
    TRANSMISSION = "Transmission"
    ANGULAR14 = "Angular14"
    ANGULAR7NF = "Angular7NF"
    ANGULAR30 = "Angular30"
    ANGULAR30_SMALLSPOT = "Angular30_SmallSpot"
    ANGULAR14_SMALLSPOT = "Angular14_SmallSpot"


class PsuMode(StrictEnum):
    HIGH = "High Pass (XPS)"
    LOW = "Low Pass (UPS)"


class PassEnergy(StrictEnum):
    E1 = "1"
    E2 = "2"
    E5 = "5"
    E10 = "10"
    E20 = "20"
    E50 = "50"
    E100 = "100"
    E200 = "200"
