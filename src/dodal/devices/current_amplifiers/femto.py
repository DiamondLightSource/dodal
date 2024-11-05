from enum import Enum

from dodal.devices.current_amplifiers.current_amplifier import CurrentAmp


class Femto3xxGainTable(str, Enum):
    """These are the sensitivity setting for Femto 3xx current amplifier"""

    sen_1 = "10^4"
    sen_2 = "10^5"
    sen_3 = "10^6"
    sen_4 = "10^7"
    sen_5 = "10^8"
    sen_6 = "10^9"
    sen_7 = "10^10"
    sen_8 = "10^11"
    sen_9 = "10^12"
    sen_10 = "10^13"


class Femto3xxGainToCurrentTable(float, Enum):
    """These are the sensitivity setting for Femto 3xx current amplifier"""

    sen_1 = 10**4
    sen_2 = 10**5
    sen_3 = 10**6
    sen_4 = 10**7
    sen_5 = 10**8
    sen_6 = 10**9
    sen_7 = 10**10
    sen_8 = 10**11
    sen_9 = 10**12
    sen_10 = 10**13


class Femto3xxRaiseTime(float, Enum):
    """These are the gain dependent raise time(s) for Femto 3xx current amplifier"""

    sen_1 = 0.8e-3
    sen_2 = 0.8e-3
    sen_3 = 0.8e-3
    sen_4 = 0.8e-3
    sen_5 = 2.3e-3
    sen_6 = 2.3e-3
    sen_7 = 17e-3
    sen_8 = 17e-3
    sen_9 = 350e-3
    sen_10 = 350e-3


class FemtoDDPCA(CurrentAmp):
    """
    Femto current amplifier device, this class should cover all DDPCA Femto current
     amplifiers, As the main different between all the DDPCA Femto is their gain table
     and respond time table.
    This class will allow the change of gain via set or the two incremental,
     increase_gain and decrease gain function.
    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        gain_table: type[Enum],
        gain_to_current_table: type[Enum],
        raise_timetable: type[Enum],
        timeout: float = 1,
        name: str = "",
    ) -> None:
        super().__init__(
            prefix=prefix,
            suffix=suffix,
            gain_table=gain_table,
            gain_to_current_table=gain_to_current_table,
            raise_timetable=raise_timetable,
            timeout=timeout,
            name=name,
        )
