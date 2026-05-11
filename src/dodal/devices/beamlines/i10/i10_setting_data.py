from ophyd_async.core import StrictEnum


class I10Grating(StrictEnum):
    AU_400 = "400 line/mm Au"
    SI_400 = "400 line/mm Si"
    AU_1200 = "1200 line/mm Au"
