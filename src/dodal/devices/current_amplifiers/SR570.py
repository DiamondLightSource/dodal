import asyncio
from enum import Enum

from ophyd_async.core import AsyncStatus, ConfigSignal, soft_signal_r_and_setter
from ophyd_async.epics.signal import epics_signal_rw

from dodal.devices.current_amplifiers.current_amplifier import CurrentAmp
from dodal.log import LOGGER


class SR570GainTable(str, Enum):
    """These are the sensitivity setting for Femto 3xx current amplifier"""

    sen_1 = "mA/V"
    sen_2 = "uA/V"
    sen_3 = "nA/V"
    sen_4 = "pA/V"


class SR570RaiseTimeTable(float, Enum):
    """These are the gain dependent raise time(s) for Femto 3xx current amplifier"""

    sen_1 = 1e-4
    sen_2 = 1e-2
    sen_3 = 0.15
    sen_4 = 0.2


class SR570FineGainTable(str, Enum):
    """These are the sensitivity setting for Femto 3xx current amplifier"""

    sen_1 = "1"
    sen_2 = "2"
    sen_3 = "5"
    sen_4 = "10"
    sen_5 = "20"
    sen_6 = "50"
    sen_7 = "100"
    sen_8 = "200"
    sen_9 = "500"


class SR570FullGainTable(Enum):
    sen_1 = [SR570GainTable.sen_1, SR570FineGainTable.sen_1]
    sen_2 = [SR570GainTable.sen_2, SR570FineGainTable.sen_9]
    sen_3 = [SR570GainTable.sen_2, SR570FineGainTable.sen_8]
    sen_4 = [SR570GainTable.sen_2, SR570FineGainTable.sen_7]
    sen_5 = [SR570GainTable.sen_2, SR570FineGainTable.sen_6]
    sen_6 = [SR570GainTable.sen_2, SR570FineGainTable.sen_5]
    sen_7 = [SR570GainTable.sen_2, SR570FineGainTable.sen_4]
    sen_8 = [SR570GainTable.sen_2, SR570FineGainTable.sen_3]
    sen_9 = [SR570GainTable.sen_2, SR570FineGainTable.sen_2]
    sen_10 = [SR570GainTable.sen_2, SR570FineGainTable.sen_1]
    sen_11 = [SR570GainTable.sen_3, SR570FineGainTable.sen_9]
    sen_12 = [SR570GainTable.sen_3, SR570FineGainTable.sen_8]
    sen_13 = [SR570GainTable.sen_3, SR570FineGainTable.sen_7]
    sen_14 = [SR570GainTable.sen_3, SR570FineGainTable.sen_6]
    sen_15 = [SR570GainTable.sen_3, SR570FineGainTable.sen_5]
    sen_16 = [SR570GainTable.sen_3, SR570FineGainTable.sen_4]
    sen_17 = [SR570GainTable.sen_3, SR570FineGainTable.sen_3]
    sen_18 = [SR570GainTable.sen_3, SR570FineGainTable.sen_2]
    sen_19 = [SR570GainTable.sen_3, SR570FineGainTable.sen_1]
    sen_20 = [SR570GainTable.sen_4, SR570FineGainTable.sen_9]
    sen_21 = [SR570GainTable.sen_4, SR570FineGainTable.sen_8]
    sen_22 = [SR570GainTable.sen_4, SR570FineGainTable.sen_7]
    sen_23 = [SR570GainTable.sen_4, SR570FineGainTable.sen_6]
    sen_24 = [SR570GainTable.sen_4, SR570FineGainTable.sen_5]
    sen_25 = [SR570GainTable.sen_4, SR570FineGainTable.sen_4]
    sen_26 = [SR570GainTable.sen_4, SR570FineGainTable.sen_3]
    sen_27 = [SR570GainTable.sen_4, SR570FineGainTable.sen_2]
    sen_28 = [SR570GainTable.sen_4, SR570FineGainTable.sen_1]


class SR570GainToCurrentTable(float, Enum):
    sen_1 = 1e3
    sen_2 = 2e3
    sen_3 = 5e3
    sen_4 = 1e4
    sen_5 = 2e4
    sen_6 = 5e4
    sen_7 = 1e5
    sen_8 = 2e5
    sen_9 = 5e5
    sen_10 = 1e6
    sen_11 = 2e6
    sen_12 = 5e6
    sen_13 = 1e7
    sen_14 = 2e7
    sen_15 = 5e7
    sen_16 = 1e8
    sen_17 = 2e8
    sen_18 = 5e8
    sen_19 = 1e9
    sen_20 = 2e9
    sen_21 = 5e9
    sen_22 = 1e10
    sen_23 = 2e9
    sen_24 = 5e9
    sen_25 = 1e11
    sen_26 = 2e9
    sen_27 = 5e9
    sen_28 = 1e12


class SR570(CurrentAmp):
    """
    SR570 current amplifier device.
    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        gain_table: type[Enum],
        fine_gain_table: type[Enum],
        full_gain_table: type[Enum],
        gain_to_current_table: type[Enum],
        raise_timetable: type[Enum],
        timeout: float = 1,
        name: str = "",
    ) -> None:
        super().__init__(
            prefix=prefix,
            suffix=suffix + "2",
            gain_table=full_gain_table,
            gain_to_current_table=gain_to_current_table,
            raise_timetable=raise_timetable,
            timeout=timeout,
            name=name,
        )
        with self.add_children_as_readables():
            self.gain, self._set_gain = soft_signal_r_and_setter(
                full_gain_table
            )  # overriding gain as there are 2 gain setting rather than just 1.

        with self.add_children_as_readables(ConfigSignal):
            self.fine_gain = epics_signal_rw(fine_gain_table, prefix + suffix + "1")
            self.coarse_gain = epics_signal_rw(gain_table, prefix + suffix + "2")

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        if value not in self.gain_table.__members__:
            raise ValueError(f"Gain value {value} is not within {self.name} range.")
        LOGGER.info(f"{self.name} gain change to {value}")
        gain, fine_gain = self.gain_table[value].value
        print(gain, fine_gain)
        await asyncio.gather(
            self.coarse_gain.set(value=gain, timeout=self.timeout),
            self.fine_gain.set(value=fine_gain, timeout=self.timeout),
        )
        self._set_gain(self.gain_table[value])
        # wait for current amplifier to settle
        await asyncio.sleep(self.raise_timetable[gain.name].value)