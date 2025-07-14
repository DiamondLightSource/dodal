from ophyd_async.core import StrictEnum


class LensMode(StrictEnum):
    TRANSMISSION = "Transmission"
    ANGULAR14 = "Angular14"
    ANGULAR7NF = "Angular7NF"
    ANGULAR30 = "Angular30"
    ANGULAR30_SMALLSPOT = "Angular30_SmallSpot"
    ANGULAR14_SMALLSPOT = "Angular14_SmallSpot"
