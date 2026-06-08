from ophyd_async.core import StrictEnum


class Grating(StrictEnum):
    PT_400 = "400 lines/mm"
    C_1600 = "C 1600 lines/mm"
    RH_1600 = "Rh 1600 lines/mm"
    PT_800 = "B 800 lines/mm"


class M3MJ6Mirror(StrictEnum):
    UNKNOWN = "Unknown"
    MJ6 = "MJ6"
    M3 = "M3"
    REFERENCE = "Reference"


class M4M5Mirror(StrictEnum):
    UNKNOWN = "Unknown"
    M4 = "M4"
    M5 = "M5"
    REFERENCE = "Reference"


class Mj7j8Mirror(StrictEnum):
    UNKNOWN = "Unknown"
    MJ8 = "MJ8"
    MJ7 = "MJ7"
    REFERENCE = "Reference"


class LensMode(StrictEnum):
    L4_ANG0_D8 = "L4Ang0d8"
    L4_ANG1_D6 = "L4Ang1d6"
    L4_ANG3_D9 = "L4Ang3d9"
    L4M_ANG0_D7 = "L4MAng0d7"
    L4M_SPAT_5 = "L4MSpat5"


class PassEnergy(StrictEnum):
    PE001 = "PE001"
    PE002 = "PE002"
    PE005 = "PE005"
    PE010 = "PE010"
    PE020 = "PE020"
    PE050 = "PE050"
    PE100 = "PE100"
    PE200 = "PE200"
