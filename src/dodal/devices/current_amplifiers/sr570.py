import asyncio
from enum import Enum

from ophyd_async.core import (
    AsyncStatus,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.current_amplifiers.current_amplifier import CurrentAmp
from dodal.log import LOGGER


class SR570GainTable(StrictEnum):
    """Coarse/unit sensitivity setting for SR570 current amplifier"""

    SEN_1 = "mA/V"
    SEN_2 = "uA/V"
    SEN_3 = "nA/V"
    SEN_4 = "pA/V"


class SR570FineGainTable(StrictEnum):
    """Fine sensitivity setting for SR570 current amplifier"""

    SEN_1 = "1"
    SEN_2 = "2"
    SEN_3 = "5"
    SEN_4 = "10"
    SEN_5 = "20"
    SEN_6 = "50"
    SEN_7 = "100"
    SEN_8 = "200"
    SEN_9 = "500"


class SR570RaiseTimeTable(float, Enum):
    """These are the gain dependent raise time(s) for SR570 current amplifier"""

    SEN_1 = 1e-4
    SEN_2 = 1e-2
    SEN_3 = 0.15
    SEN_4 = 0.2


class SR570FullGainTable(Enum):
    """Combined gain table, as each gain step is a combination of both coarse gain and
    fine gain setting"""

    SEN_1 = [SR570GainTable.SEN_1, SR570FineGainTable.SEN_1]
    SEN_2 = [SR570GainTable.SEN_2, SR570FineGainTable.SEN_9]
    SEN_3 = [SR570GainTable.SEN_2, SR570FineGainTable.SEN_8]
    SEN_4 = [SR570GainTable.SEN_2, SR570FineGainTable.SEN_7]
    SEN_5 = [SR570GainTable.SEN_2, SR570FineGainTable.SEN_6]
    SEN_6 = [SR570GainTable.SEN_2, SR570FineGainTable.SEN_5]
    SEN_7 = [SR570GainTable.SEN_2, SR570FineGainTable.SEN_4]
    SEN_8 = [SR570GainTable.SEN_2, SR570FineGainTable.SEN_3]
    SEN_9 = [SR570GainTable.SEN_2, SR570FineGainTable.SEN_2]
    SEN_10 = [SR570GainTable.SEN_2, SR570FineGainTable.SEN_1]
    SEN_11 = [SR570GainTable.SEN_3, SR570FineGainTable.SEN_9]
    SEN_12 = [SR570GainTable.SEN_3, SR570FineGainTable.SEN_8]
    SEN_13 = [SR570GainTable.SEN_3, SR570FineGainTable.SEN_7]
    SEN_14 = [SR570GainTable.SEN_3, SR570FineGainTable.SEN_6]
    SEN_15 = [SR570GainTable.SEN_3, SR570FineGainTable.SEN_5]
    SEN_16 = [SR570GainTable.SEN_3, SR570FineGainTable.SEN_4]
    SEN_17 = [SR570GainTable.SEN_3, SR570FineGainTable.SEN_3]
    SEN_18 = [SR570GainTable.SEN_3, SR570FineGainTable.SEN_2]
    SEN_19 = [SR570GainTable.SEN_3, SR570FineGainTable.SEN_1]
    SEN_20 = [SR570GainTable.SEN_4, SR570FineGainTable.SEN_9]
    SEN_21 = [SR570GainTable.SEN_4, SR570FineGainTable.SEN_8]
    SEN_22 = [SR570GainTable.SEN_4, SR570FineGainTable.SEN_7]
    SEN_23 = [SR570GainTable.SEN_4, SR570FineGainTable.SEN_6]
    SEN_24 = [SR570GainTable.SEN_4, SR570FineGainTable.SEN_5]
    SEN_25 = [SR570GainTable.SEN_4, SR570FineGainTable.SEN_4]
    SEN_26 = [SR570GainTable.SEN_4, SR570FineGainTable.SEN_3]
    SEN_27 = [SR570GainTable.SEN_4, SR570FineGainTable.SEN_2]
    SEN_28 = [SR570GainTable.SEN_4, SR570FineGainTable.SEN_1]


class SR570GainToCurrentTable(float, Enum):
    """Conversion table for gain(sen) to current"""

    SEN_1 = 1e3
    SEN_2 = 2e3
    SEN_3 = 5e3
    SEN_4 = 1e4
    SEN_5 = 2e4
    SEN_6 = 5e4
    SEN_7 = 1e5
    SEN_8 = 2e5
    SEN_9 = 5e5
    SEN_10 = 1e6
    SEN_11 = 2e6
    SEN_12 = 5e6
    SEN_13 = 1e7
    SEN_14 = 2e7
    SEN_15 = 5e7
    SEN_16 = 1e8
    SEN_17 = 2e8
    SEN_18 = 5e8
    SEN_19 = 1e9
    SEN_20 = 2e9
    SEN_21 = 5e9
    SEN_22 = 1e10
    SEN_23 = 2e10
    SEN_24 = 5e10
    SEN_25 = 1e11
    SEN_26 = 2e11
    SEN_27 = 5e11
    SEN_28 = 1e12


class SR570(CurrentAmp):
    """
    SR570 current amplifier device. This is similar to Femto with the only different
     is SR570 has two gain setting fine and coarse, therefore it requires extra
     gain tables.
    Attributes:
        fine_gain (SignalRW): This is the epic signal that control SR570 fine gain.
        coarse_gain (SignalRW): This is the epic signal that control SR570 coarse gain.
        fine_gain_table (strictEnum): The table that fine_gain use to set gain.
        coarse_gain_table (strictEnum): The table that coarse_gain use to set gain.
        timeout (float): Maximum waiting time in second for setting gain.
        raise_timetable (Enum): Table contain the amount of time to wait after
            setting gain.
        combined_table (Enum): Table that combine fine and coarse table into one.
        gain (SignalRW([str]): Soft signal to store the member name of the current gain
            setting in gain_conversion_table.
        upperlimit (float): upperlimit of the current amplifier
        lowerlimit (float): lowerlimit of the current amplifier

    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        fine_gain_table: type[StrictEnum],
        coarse_gain_table: type[StrictEnum],
        combined_table: type[Enum],
        gain_to_current_table: type[Enum],
        raise_timetable: type[Enum],
        upperlimit: float = 4.8,
        lowerlimit: float = 0.4,
        timeout: float = 1,
        name: str = "",
    ) -> None:
        super().__init__(name=name, gain_conversion_table=gain_to_current_table)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.fine_gain = epics_signal_rw(fine_gain_table, prefix + suffix + "1")
            self.coarse_gain = epics_signal_rw(coarse_gain_table, prefix + suffix + "2")

        self.fine_gain_table = fine_gain_table
        self.coarse_gain_table = coarse_gain_table
        self.timeout = timeout
        self.raise_timetable = raise_timetable
        self.combined_table = combined_table
        self.upperlimit = upperlimit
        self.lowerlimit = lowerlimit

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        if value not in [item.value for item in self.gain_conversion_table]:
            raise ValueError(
                f"Gain value {value} is not within {self.name} range."
                + "\n Available gain:"
                + f" {[f'{c.value:.0e}' for c in self.gain_conversion_table]}"
            )
        SEN_setting = self.gain_conversion_table(value).name
        LOGGER.info(f"{self.name} gain change to {value}")

        coarse_gain, fine_gain = self.combined_table[SEN_setting].value
        await asyncio.gather(
            self.fine_gain.set(value=fine_gain, timeout=self.timeout),
            self.coarse_gain.set(value=coarse_gain, timeout=self.timeout),
        )
        await asyncio.sleep(self.raise_timetable[coarse_gain.name].value)

    async def increase_gain(self, value=3) -> None:
        current_gain = int((await self.get_gain()).name.split("_")[-1])
        current_gain += value
        if current_gain > len(self.combined_table):
            await self.set(
                self.gain_conversion_table[f"SEN_{len(self.combined_table)}"]
            )
            raise ValueError("Gain at max value")
        await self.set(self.gain_conversion_table[f"SEN_{current_gain}"])

    async def decrease_gain(self, value=3) -> None:
        current_gain = int((await self.get_gain()).name.split("_")[-1])
        current_gain -= value
        if current_gain < 1:
            await self.set(self.gain_conversion_table["SEN_1"])
            raise ValueError("Gain at min value")
        await self.set(self.gain_conversion_table[f"SEN_{current_gain}"])

    async def get_gain(self) -> Enum:
        result = await asyncio.gather(
            self.coarse_gain.get_value(), self.fine_gain.get_value()
        )
        return self.gain_conversion_table[self.combined_table(result).name]

    async def get_upperlimit(self) -> float:
        return self.upperlimit

    async def get_lowerlimit(self) -> float:
        return self.lowerlimit
