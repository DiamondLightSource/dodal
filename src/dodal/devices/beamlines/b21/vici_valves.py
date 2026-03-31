from ophyd_async.core import OnOff, StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw, epics_signal_rw_rbv


class Valve1Positions(StrictEnum):
    POS_1 = "Sep300"
    POS_2 = "KW402.5"
    POS_3 = "S200"
    POS_4 = "Sup6"
    POS_5 = "Guest1"
    POS_6 = "Bypass1"


class Valve2Positions(StrictEnum):
    POS_1 = "KW403"
    POS_2 = "KW402.5"
    POS_3 = "S200"
    POS_4 = "Sep500"
    POS_5 = "Guest2"
    POS_6 = "Bypass2"


class ViciValves(StandardReadable):
    """The vici valves select what liquid is flowing through the HPLC.

    If the auto_select PV is on it is expected that DAQ will control the valves,
    otherwise these will be controlled directly through EPICS by beamline staff.
    """

    def __init__(self, prefix: str, auto_select_prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.valve_1 = epics_signal_rw_rbv(
                Valve1Positions, prefix + "VALVE1:POSN", ":RBV"
            )
            self.valve_2 = epics_signal_rw_rbv(
                Valve2Positions, prefix + "VALVE2:POSN", ":RBV"
            )

        self.auto_select = epics_signal_rw(OnOff, auto_select_prefix + "AUTO_SELECT")
        super().__init__(name)
