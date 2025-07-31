from ophyd_async.core import StrictEnum


class OnState(StrictEnum):
    ON = "On"
    OFF = "OFF"


class OnStateCapitalised(StrictEnum):
    ON = "ON"
    OFF = "OFF"


class EnabledState(StrictEnum):
    ENABLED = "Enabled"
    DISABLED = "Disabled"


class EnabledStateCapitalised(StrictEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class InOut(StrictEnum):
    IN = "In"
    OUT = "Out"


class InOutCapitalised(StrictEnum):
    IN = "IN"
    OUT = "OUT"
