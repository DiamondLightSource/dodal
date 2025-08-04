from ophyd_async.core import StrictEnum


class OnStateCapitalised(StrictEnum):
    ON = "ON"
    OFF = "OFF"


class EnabledStateCapitalised(StrictEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class InStateCapitalised(StrictEnum):
    IN = "IN"
    OUT = "OUT"
