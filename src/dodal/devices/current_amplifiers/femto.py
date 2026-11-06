import asyncio
from enum import Enum

from ophyd_async.core import StandardReadableFormat, StrictEnum, derived_signal_rw
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.current_amplifiers import CurrentAmp
from dodal.log import LOGGER


class Femto3xxGainTable(StrictEnum):
    """These are the sensitivity setting for Femto 3xx current amplifier."""

    SEN_1 = "10^4"
    SEN_2 = "10^5"
    SEN_3 = "10^6"
    SEN_4 = "10^7"
    SEN_5 = "10^8"
    SEN_6 = "10^9"
    SEN_7 = "10^10"
    SEN_8 = "10^11"
    SEN_9 = "10^12"
    SEN_10 = "10^13"


class Femto3xxRaiseTime(float, Enum):
    """These are the gain dependent raise time(s) for Femto 3xx current amplifier."""

    SEN_1 = 0.8e-3
    SEN_2 = 0.8e-3
    SEN_3 = 0.8e-3
    SEN_4 = 0.8e-3
    SEN_5 = 2.3e-3
    SEN_6 = 2.3e-3
    SEN_7 = 17e-3
    SEN_8 = 17e-3
    SEN_9 = 350e-3
    SEN_10 = 350e-3


FEMTO3XX_GAIN_CONFIGURATION: dict[Femto3xxGainTable, float] = {
    Femto3xxGainTable.SEN_1: 1e4,
    Femto3xxGainTable.SEN_2: 1e5,
    Femto3xxGainTable.SEN_3: 1e6,
    Femto3xxGainTable.SEN_4: 1e7,
    Femto3xxGainTable.SEN_5: 1e8,
    Femto3xxGainTable.SEN_6: 1e9,
    Femto3xxGainTable.SEN_7: 1e10,
    Femto3xxGainTable.SEN_8: 1e11,
    Femto3xxGainTable.SEN_9: 1e12,
    Femto3xxGainTable.SEN_10: 1e13,
}


def _gain_to_sensitivity(
    gain_setting: Femto3xxGainTable,
) -> float:
    """Convert Femto gain setting to sensitivity in V/A."""
    return FEMTO3XX_GAIN_CONFIGURATION[gain_setting]


class FemtoDDPCA(CurrentAmp):
    """Femto current amplifier with derived numerical sensitivity."""

    def __init__(
        self,
        prefix: str,
        suffix: str,
        upperlimit: float = 8.8,
        lowerlimit: float = 0.68,
        timeout: float = 1,
        name: str = "",
    ) -> None:
        self.timeout = timeout
        self.gain_configuration = FEMTO3XX_GAIN_CONFIGURATION
        self.raise_timetable = Femto3xxRaiseTime

        self.gain_setting = epics_signal_rw(Femto3xxGainTable, prefix + suffix)

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.gain = derived_signal_rw(
                _gain_to_sensitivity, self._set_gain, gain_setting=self.gain_setting
            )

        super().__init__(upperlimit=upperlimit, lowerlimit=lowerlimit, name=name)

    async def _set_gain(self, value: float) -> None:
        """Set sensitivity in V/A."""
        gain_setting = next(
            (
                setting
                for setting, sensitivity in self.gain_configuration.items()
                if sensitivity == value
            ),
            None,
        )

        if gain_setting is None:
            available = [
                f"{sensitivity:.0e}" for sensitivity in self.gain_configuration.values()
            ]
            raise ValueError(
                f"Gain value {value} is not within {self.name} range.\n"
                f"Available gains: {available}"
            )

        LOGGER.info("%s gain change to %s:%s", self.name, gain_setting.name, value)

        await self.gain_setting.set(gain_setting, timeout=self.timeout)

        await asyncio.sleep(self.raise_timetable[gain_setting.name].value)

    async def increase_gain(self, value: int = 1) -> bool:
        current_gain = await self.gain.get_value()
        gains = sorted(self.gain_configuration.values())
        target_index = gains.index(current_gain) + value

        if target_index >= len(gains):
            return False

        await self.set(gains[target_index])
        return True

    async def decrease_gain(self, value: int = 1) -> bool:
        current_gain = await self.gain.get_value()
        gains = sorted(self.gain_configuration.values())
        target_index = gains.index(current_gain) - value

        if target_index < 0:
            return False

        await self.set(gains[target_index])
        return True
