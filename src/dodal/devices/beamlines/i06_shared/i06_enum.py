from ophyd_async.core import StrictEnum


class I06Grating(StrictEnum):
    GRATING_150 = "150 lines/mm"
    GRATING_400 = "400 lines/mm"
    GRATING_1200 = "1200 lines/mm"
