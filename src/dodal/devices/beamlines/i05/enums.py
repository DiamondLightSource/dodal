from ophyd_async.core import StrictEnum


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


# ToDo
class PsuMode(StrictEnum):
    UNKNOWN = "UNKNOWN"
