from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.positioner import create_positioner


class FilterAValues(StrictEnum):
    """Maps from a short usable name to the string name in EPICS"""

    AL_2MM = "2 mm Al"
    AL_1_5MM = "1.5 mm Al"
    AL_1_25MM = "1.25 mm Al"
    AL_0_8MM = "0.8 mm Al"
    AL_0_55MM = "0.55 mm Al"
    AL_0_5MM = "0.5 mm Al"
    AL_0_3MM = "0.3 mm Al"
    AL_0_25MM = "0.25 mm Al"
    AL_0_15MM = "0.15 mm Al"
    AL_0_1MM = "0.1 mm Al"
    AL_0_05MM = "0.05 mm Al"
    AL_0_025MM = "0.025 mm Al"
    AL_GAP = "Gap"


class FilterBValues(StrictEnum):
    DIAMOND_THIN = "Diamond thin"
    DIAMOND_THICK = "Diamond thick"
    NI_DRAIN = "ni drain"
    AU_DRAIN = "au drain"
    AL_DRAIN = "al drain"
    GAP = "Gap"
    IN_LINE_DIODE = "in line diode"


class Diode(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.signal = epics_signal_r(float, prefix + "B:DIODE:I")
            # self.positioner_a = create_positioner(FilterAValues, prefix + "A:POSN", positioner_pv_suffix=":MP.SELECT")
            # self.positioner_b = create_positioner(FilterBValues, prefix + "B:POSN", positioner_pv_suffix=":MP.SELECT")
            self.positioner_a = create_positioner(FilterAValues, prefix + "A:POSN") # this one connects in all but the MP:SELECT setup
            self.positioner_b = create_positioner(FilterBValues, prefix + "B:POSN") # this one connects in all but the MP:SELECT setup
            # self.positioner_a = create_positioner(FilterAValues, prefix + "A:MP", positioner_pv_suffix="")
            # self.positioner_b = create_positioner(FilterBValues, prefix + "B:MP")

        super().__init__(name=name)
