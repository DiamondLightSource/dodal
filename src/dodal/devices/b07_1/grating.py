from ophyd_async.core import StrictEnum


class B07CGrating(StrictEnum):
    AU_400 = "400 l/mm Au"
    AU_600 = "600 l/mm Au"
    PT_600 = "600 l/mm Pt"
    AU_1200 = "1200 l/mm Au"
    ML_1200 = "1200 l/mm ML"
    NO_GRATING = "No Grating"
