from ophyd_async.core import StrictEnum


class Grating(StrictEnum):
    AU_400 = "400 l/mm Au"
    AU_600 = "600 l/mm Au"
    PT_600 = "600 l/mm Pt"
    AU_1200 = "1200 l/mm Au"
    ML_1200 = "1200 l/mm ML"
    NO_GRATING = "No Grating"


class LensMode(StrictEnum):
    SMALL_AREA = "SmallArea"
    ANGLE_RESOLVED_MODE_22 = "AngleResolvedMode22"
    ANGLE_RESOLVED_MODE_30 = "AngleResolvedMode30"
    LARGE_AREA = "LargeArea"
