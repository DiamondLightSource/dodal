from ophyd_async.core import StrictEnum, SupersetEnum


class Grating(StrictEnum):
    AU_400 = "400 l/mm Au"
    AU_600 = "600 l/mm Au"
    PT_600 = "600 l/mm Pt"
    AU_1200 = "1200 l/mm Au"
    ML_1200 = "1200 l/mm ML"
    NO_GRATING = "No Grating"


class LensMode(SupersetEnum):
    SMALL_AREA = "SmallArea"
    ANGLE_RESOLVED_MODE_22 = "AngleResolvedMode22"
    ANGLE_RESOLVED_MODE_30 = "AngleResolvedMode30"
    LARGE_AREA = "LargeArea"
    # This is connected to the device separately and will only have "Not connected" as
    # option if disconnected. Once it is connected, "Not connected" is replaced with the
    # options above. This is also why this must be a SupersetEnum.
    NOT_CONNECTED = "Not connected"
