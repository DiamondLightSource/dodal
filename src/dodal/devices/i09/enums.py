from ophyd_async.core import StrictEnum


class Grating(StrictEnum):
    G_300 = "300 lines/mm"
    G_400 = "400 lines/mm"
    G_800 = "800 lines/mm"


class LensMode(StrictEnum):
    TRANSMISSION = "Transmission"
    ANGULAR45 = "Angular45"
    ANGULAR60 = "Angular60"
    ANGULAR56 = "Angular56"
    ANGULAR45VUV = "Angular45VUV"
