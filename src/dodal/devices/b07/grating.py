from ophyd_async.core import StrictEnum


class B07Grating(StrictEnum):
    NI_400 = "400 l/mm Ni"
    NI_1000 = "1000 l/mm Ni"
    PT_600 = "BAD 600 l/mm Pt"
    AU_600 = "600 l/mm Au"
    NO_GRATING = "No Grating"
