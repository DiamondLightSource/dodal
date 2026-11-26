from ophyd_async.core import StrictEnum


class Grating(StrictEnum):
    PGM_600 = "600 lines/mm"
    PGM_400 = "400 lines/mm"
    PGM_300 = "300 lines/mm"
