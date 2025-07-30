from ophyd_async.core import StrictEnum


class OnState(StrictEnum):
    ON = "On"
    OFF = "OFF"


class OnStateCaptilised(StrictEnum):
    ON = "ON"
    OFF = "OFF"


class EnabledState(StrictEnum):
    ENABLED = "Enabled"
    DISABLED = "Disabled"


class EnabledStateCaptilised(StrictEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class InOut(StrictEnum):
    IN = "In"
    OUT = "Out"


class InOutCapitlised(StrictEnum):
    IN = "IN"
    OUT = "OUT"
