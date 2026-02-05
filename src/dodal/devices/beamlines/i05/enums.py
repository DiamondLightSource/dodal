from ophyd_async.core import StrictEnum


class Grating(StrictEnum):
    PT_400 = "400 lines/mm"
    C_1600 = "C 1600 lines/mm"
    RH_1600 = "Rh 1600 lines/mm"
    PT_800 = "B 800 lines/mm"


class M3MJ6Mirror(StrictEnum):
    UNKNOWN = "Unknown"
    MJ6 = "MJ6"
    M3 = "M3"
    REFERENCE = "Reference"


class M4M5Mirror(StrictEnum):
    UNKNOWN = "Unknown"
    M4 = "M4"
    M5 = "M5"
    REFERENCE = "Reference"


class Mj7j8Mirror(StrictEnum):
    UNKNOWN = "Unknown"
    MJ8 = "MJ8"
    MJ7 = "MJ7"
    REFERENCE = "Reference"
