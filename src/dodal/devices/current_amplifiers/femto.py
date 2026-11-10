import asyncio
from collections.abc import Mapping
from enum import Enum
from typing import Generic, TypeVar

from ophyd_async.core import (
    EnumTypes,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_rw,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.current_amplifiers import CurrentAmp
from dodal.log import LOGGER


class Femto3xxGainTable(StrictEnum):
    """Sensitivity setting for Femto 3xx current amplifier."""

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
    """Gain dependent raise time(s) for Femto 3xx current amplifier."""

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


DEFAULT_FEMTO3XX_GAIN_TO_VALUE: dict[Femto3xxGainTable, float] = {
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


EnumTypesT = TypeVar("EnumTypesT", bound=EnumTypes)


class FemtoDDPCA(CurrentAmp, Generic[EnumTypesT]):
    """Femto current amplifier with derived numerical sensitivity.

    The Femto amplifier exposes its gain as an EPICS enumeration via gain_setting. This
    device provides a derived numerical gain signal representing the current-to-voltage
    sensitivity in V/A, using the Femto gain configuration table.

    Attributes:
        gain (SignalRW[float]): Derived current-to-voltage sensitivity in V/A.
        gain_enum (SignalRW[Femto3xxGainTable]): EPICS signal controlling the amplifier
            gain setting via enum.
        upperlimit (SignalRW[float]): Upper output voltage threshold in V used by
            automatic gain adjustment.
        lowerlimit (SignalRW[float]): Lower output voltage threshold in V used by
            automatic gain adjustment.
    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        gain_enum_type: type[EnumTypesT] = Femto3xxGainTable,
        gain_to_value_config: Mapping[
            EnumTypesT, float
        ] = DEFAULT_FEMTO3XX_GAIN_TO_VALUE,
        raise_timetable: type[Enum] = Femto3xxRaiseTime,
        upperlimit: float = 8.8,
        lowerlimit: float = 0.68,
        timeout: float = 1,
        name: str = "",
    ) -> None:
        """Configure the Femto current amplifier.

        Args:
            prefix: EPICS PV prefix for the amplifier.
            suffix: EPICS PV suffix for the gain setting.
            gain_enum_type: Enum type used for the amplifier's gain settings.
            gain_to_value_config: Mapping of gain enum members to sensitivity values in V/A.
            raise_timetable: Table defining the settling time associated with each gain
                setting.
            upperlimit: Upper output voltage threshold in V for automatic gain
                adjustment.
            lowerlimit: Lower output voltage threshold in V for automatic gain
                adjustment.
            timeout: Maximum waiting time in seconds when setting gain.
            name: Name of the device.
        """
        self._gain_to_value_config = gain_to_value_config
        # Create the inverse lookup table for _set_gain method.
        self._value_to_gain_config = {
            sensitivity: setting
            for setting, sensitivity in self._gain_to_value_config.items()
        }
        self._raise_timetable = raise_timetable
        self._timeout = timeout

        self.gain_enum = epics_signal_rw(gain_enum_type, prefix + suffix)

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.gain = derived_signal_rw(
                self._gain_enum_to_value, self._set_gain, gain_enum=self.gain_enum
            )
        super().__init__(upperlimit=upperlimit, lowerlimit=lowerlimit, name=name)

    def _gain_enum_to_value(self, gain_enum: EnumTypesT) -> float:
        """Convert Femto gain enum to numerical value V/A."""
        return self._gain_to_value_config[gain_enum]

    async def _set_gain(self, value: float) -> None:
        """Set sensitivity in V/A."""
        try:
            gain_enum = self._value_to_gain_config[value]
        except KeyError:
            available = [
                f"{sensitivity:.0e}"
                for sensitivity in self._value_to_gain_config.keys()
            ]
            raise ValueError(
                f"Gain value {value} is not within {self.name} range.\n"
                f"Available gains: {available}"
            ) from None

        LOGGER.info("%s gain change to %s:%s", self.name, gain_enum.name, value)
        await self.gain_enum.set(gain_enum, timeout=self._timeout)
        await asyncio.sleep(self._raise_timetable[gain_enum.name].value)

    async def increase_gain(self, value: int = 1) -> bool:
        current_gain = await self.gain.get_value()
        gains = sorted(self._gain_to_value_config.values())
        target_index = gains.index(current_gain) + value

        if target_index >= len(gains):
            return False

        await self.set(gains[target_index])
        return True

    async def decrease_gain(self, value: int = 1) -> bool:
        current_gain = await self.gain.get_value()
        gains = sorted(self._gain_to_value_config.values())
        target_index = gains.index(current_gain) - value

        if target_index < 0:
            return False

        await self.set(gains[target_index])
        return True
