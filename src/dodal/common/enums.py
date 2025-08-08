from ophyd_async.core import StrictEnum

# Any capitalised enums needs to be removed and replaced with ones from ophyd-async.core
# https://github.com/DiamondLightSource/dodal/issues/1416


class OnOffUpper(StrictEnum):
    ON = "ON"
    OFF = "OFF"


class EnabledDisabledUpper(StrictEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class InOutUpper(StrictEnum):
    IN = "IN"
    OUT = "OUT"
