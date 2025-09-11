from ophyd_async.core import StrictEnum


class Grating(StrictEnum):
    G_150 = "150 lines/mm"
    G_400 = "400 lines/mm"
    G_1200 = "1200 lines/mm"
