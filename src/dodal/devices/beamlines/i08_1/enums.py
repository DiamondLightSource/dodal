from ophyd_async.core import SubsetEnum


class Grating(SubsetEnum):
    PGM_600 = "600 lines/mm"
    PGM_400 = "400 lines/mm"
    PGM_300 = "300 lines/mm"
