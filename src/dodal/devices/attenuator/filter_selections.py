from ophyd_async.core import SubsetEnum


class P99FilterSelections(SubsetEnum):
    EMPTY = "Empty"
    MN5UM = "Mn 5um"
    FE = "Fe (empty)"
    CO5UM = "Co 5um"
    NI5UM = "Ni 5um"
    CU5UM = "Cu 5um"
    ZN5UM = "Zn 5um"
    ZR = "Zr (empty)"
    MO = "Mo (empty)"
    RH = "Rh (empty)"
    PD = "Pd (empty)"
    AG = "Ag (empty)"
    CD25UM = "Cd 25um"
    W = "W (empty)"
    PT = "Pt (empty)"
    USER = "User"


class I02_1FilterOneSelections(SubsetEnum):
    EMPTY = "Empty"
    AL8 = "Al8"
    AL15 = "Al15"
    AL25 = "Al25"
    AL1000 = "Al1000"
    TI50 = "Ti50"
    TI100 = "Ti100"
    TI200 = "Ti200"
    TI400 = "Ti400"
    TWO_TIMES_TI500 = "2xTi500"


class I02_1FilterTwoSelections(SubsetEnum):
    EMPTY = "Empty"
    AL50 = "Al50"
    AL100 = "Al100"
    AL125 = "Al125"
    AL250 = "Al250"
    AL500 = "Al500"
    AL1000 = "Al1000"
    TI50 = "Ti50"
    TI100 = "Ti100"
    TWO_TIMES_TI500 = "2xTi500"


class I02_1FilterThreeSelections(SubsetEnum):
    EMPTY = "Empty"
    AL15 = "Al15"
    AL25 = "Al25"
    AL50 = "Al50"
    AL100 = "Al100"
    AL250 = "Al250"
    AL1000 = "Al1000"
    TI50 = "Ti50"
    TI100 = "Ti100"
    TI200 = "Ti200"


class I02_1FilterFourSelections(SubsetEnum):
    EMPTY = "Empty"
    AL15 = "Al15"
    AL25 = "Al25"
    AL50 = "Al50"
    AL100 = "Al100"
    AL250 = "Al250"
    AL500 = "Al500"
    TI300 = "Ti300"
    TI400 = "Ti400"
    TI500 = "Ti500"
