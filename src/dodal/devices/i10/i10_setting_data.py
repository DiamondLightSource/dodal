from ophyd_async.core import StrictEnum


class I10Grating(StrictEnum):
    Au400 = "400 line/mm Au"
    Si400 = "400 line/mm Si"
    Au1200 = "1200 line/mm Au"
