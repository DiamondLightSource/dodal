from ophyd_async.core import StrictEnum


class Grating(StrictEnum):
    RH_400 = "400 lines/mm"
    C_1600 = "C 1600 lines/mm"
    RH_1600 = "Rh 1600 lines/mm"
    B_800 = "B 800 lines/mm"
