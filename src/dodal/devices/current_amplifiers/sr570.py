import asyncio
from enum import Enum

from ophyd_async.core import StandardReadableFormat, StrictEnum, derived_signal_rw
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.current_amplifiers.current_amplifier import CurrentAmp
from dodal.log import LOGGER


class SR570GainTable(StrictEnum):
    """Coarse/unit sensitivity setting for SR570 current amplifier."""

    SEN_1 = "mA/V"
    SEN_2 = "uA/V"
    SEN_3 = "nA/V"
    SEN_4 = "pA/V"


class SR570FineGainTable(StrictEnum):
    """Fine sensitivity setting for SR570 current amplifier."""

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
    """Gain-dependent raise time(s) for SR570 current amplifier."""

    SEN_1 = 1e-4
    SEN_2 = 1e-2
    SEN_3 = 0.15
    SEN_4 = 0.2


SR570_GAIN_CONFIGURATION: dict[SR570GainTable, dict[SR570FineGainTable, float]] = {
    SR570GainTable.SEN_1: {
        SR570FineGainTable.SEN_1: 1e3,
    },
    SR570GainTable.SEN_2: {
        SR570FineGainTable.SEN_9: 2e3,
        SR570FineGainTable.SEN_8: 5e3,
        SR570FineGainTable.SEN_7: 1e4,
        SR570FineGainTable.SEN_6: 2e4,
        SR570FineGainTable.SEN_5: 5e4,
        SR570FineGainTable.SEN_4: 1e5,
        SR570FineGainTable.SEN_3: 2e5,
        SR570FineGainTable.SEN_2: 5e5,
        SR570FineGainTable.SEN_1: 1e6,
    },
    SR570GainTable.SEN_3: {
        SR570FineGainTable.SEN_9: 2e6,
        SR570FineGainTable.SEN_8: 5e6,
        SR570FineGainTable.SEN_7: 1e7,
        SR570FineGainTable.SEN_6: 2e7,
        SR570FineGainTable.SEN_5: 5e7,
        SR570FineGainTable.SEN_4: 1e8,
        SR570FineGainTable.SEN_3: 2e8,
        SR570FineGainTable.SEN_2: 5e8,
        SR570FineGainTable.SEN_1: 1e9,
    },
    SR570GainTable.SEN_4: {
        SR570FineGainTable.SEN_9: 2e9,
        SR570FineGainTable.SEN_8: 5e9,
        SR570FineGainTable.SEN_7: 1e10,
        SR570FineGainTable.SEN_6: 2e10,
        SR570FineGainTable.SEN_5: 5e10,
        SR570FineGainTable.SEN_4: 1e11,
        SR570FineGainTable.SEN_3: 2e11,
        SR570FineGainTable.SEN_2: 5e11,
        SR570FineGainTable.SEN_1: 1e12,
    },
}


def _gain_to_sensitivity(
    coarse_gain: SR570GainTable,
    fine_gain: SR570FineGainTable,
) -> float:
    """Calculate the SR570 sensitivity from its coarse and fine settings."""
    return SR570_GAIN_CONFIGURATION[coarse_gain][fine_gain]


class SR570(CurrentAmp):
    """SR570 current amplifier device. This is similar to Femto with the only different
    is SR570 has two gain setting fine and coarse, therefore it requires extra
    gain tables.

    Attributes:
        fine_gain (SignalRW): This is the epic signal that control SR570 fine gain.
        coarse_gain (SignalRW): This is the epic signal that control SR570 coarse gain.
        fine_gain_table (strictEnum): The table that fine_gain use to set gain.
        coarse_gain_table (strictEnum): The table that coarse_gain use to set gain.
        raise_timetable (Enum): Table contain the amount of time to wait after
            setting gain.
        combined_table (Enum): Table that combine fine and coarse table into one.
        gain (SignalRW([str]): Soft signal to store the member name of the current gain
            setting in gain_conversion_table.
        upperlimit (float): upperlimit of the current amplifier
        lowerlimit (float): lowerlimit of the current amplifier
        timeout (float): Maximum waiting time in second for setting gain.
    """

    def __init__(
        self,
        prefix: str,
        suffix: str = "SENS:SEL",
        upperlimit: float = 4.8,
        lowerlimit: float = 0.4,
        timeout: float = 1,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.fine_gain = epics_signal_rw(SR570FineGainTable, prefix + suffix + "1")
            self.coarse_gain = epics_signal_rw(SR570GainTable, prefix + suffix + "2")

        self.timeout = timeout
        self.raise_timetable = SR570RaiseTimeTable

        self.gain = derived_signal_rw(
            _gain_to_sensitivity,
            self._set_gain,
            coarse_gain=self.coarse_gain,
            fine_gain=self.fine_gain,
        )

        super().__init__(
            upperlimit=upperlimit,
            lowerlimit=lowerlimit,
            name=name,
        )

    async def _set_gain(self, value: float) -> None:
        """Set sensitivity in V/A."""
        configuration = next(
            (
                (coarse_gain, fine_gain)
                for coarse_gain, fine_gains in SR570_GAIN_CONFIGURATION.items()
                for fine_gain, sensitivity in fine_gains.items()
                if sensitivity == value
            ),
            None,
        )

        if configuration is None:
            available = [
                f"{sensitivity:.0e}"
                for fine_gains in SR570_GAIN_CONFIGURATION.values()
                for sensitivity in fine_gains.values()
            ]
            raise ValueError(
                f"Gain value {value} is not within {self.name} range.\n"
                f"Available gains: {available}"
            )

        coarse_gain, fine_gain = configuration

        LOGGER.info("%s gain change to %s", self.name, value)

        await asyncio.gather(
            self.fine_gain.set(fine_gain, timeout=self.timeout),
            self.coarse_gain.set(coarse_gain, timeout=self.timeout),
        )
        await asyncio.sleep(self.raise_timetable[coarse_gain.name].value)

    async def increase_gain(self, value: int = 3) -> None:
        current_gain = await self.gain.get_value()
        gains = sorted(
            sensitivity
            for fine_gains in SR570_GAIN_CONFIGURATION.values()
            for sensitivity in fine_gains.values()
        )
        current_index = gains.index(current_gain)
        target_index = current_index + value

        if target_index >= len(gains):
            await self.set(gains[-1])
            raise ValueError("Gain at max value")

        await self.set(gains[target_index])

    async def decrease_gain(self, value: int = 3) -> None:
        current_gain = await self.gain.get_value()
        gains = sorted(
            sensitivity
            for fine_gains in SR570_GAIN_CONFIGURATION.values()
            for sensitivity in fine_gains.values()
        )
        current_index = gains.index(current_gain)
        target_index = current_index - value

        if target_index < 0:
            await self.set(gains[0])
            raise ValueError("Gain at min value")

        await self.set(gains[target_index])
