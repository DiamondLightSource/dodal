from ophyd_async.core import StrictEnum


class Pol(StrictEnum):
    NONE = "None"
    LH = "lh"
    LV = "lv"
    PC = "pc"
    NC = "nc"
    LA = "la"
    LH3 = "lh3"
    LV3 = "lv3"


class UndulatorGateStatus(StrictEnum):
    OPEN = "Open"
    CLOSE = "Closed"
