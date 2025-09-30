from asyncio import gather

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    SignalDatatypeT,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_rw,
    soft_signal_rw,
)

from .lakeshore_io import (
    LakeshoreBaseIO,
)


class Heater336Settings(StrictEnum):
    OFF = "Off"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Lakeshore(LakeshoreBaseIO, StandardReadable, Movable[float]):
    """
    Device for controlling and reading from a Lakeshore temperature controller.
    It supports multiple channels and PID control.

    Attributes
    ----------
    temperature : LakeshoreBaseIO
        Temperature IO interface.
    PID : PIDBaseIO
        PID IO interface.
    control_channel : derived_signal_rw
        Signal for selecting the control channel,
        optional readback as hinted signal
        (default readback channel is the same as control channel).

    temperature_high_limit: soft_signal_rw
        Signal to store the soft high temperature limit.
    temperature_low_limit: soft_signal_rw
        Signal to store the soft low temperature limit.


    Methods
    -------
    set(value: float)
        Set the temperature setpoint for the selected control channel.
    """

    def __init__(
        self,
        prefix: str,
        num_readback_channel: int,
        heater_setting: type[SignalDatatypeT],
        control_channel: int = 1,
        single_control_channel: bool = False,
        name: str = "",
    ):
        """
        Parameters
        ----------
        prefix : str
            The EPICS prefix for the device.
        no_channels : int
            Number of temperature channels.
        heater_setting : type[SignalDatatypeT]
            Enum type for heater settings.
        control_channel : int, optional
            The initial control channel (default is 1).
        single_control_channel : bool, optional
            Whether to use a single control channel (default is False).
        name : str, optional
            Name of the device.
        """
        self._control_channel = soft_signal_rw(int, initial_value=control_channel)
        self.temperature_high_limit = soft_signal_rw(float, initial_value=400)
        self.temperature_low_limit = soft_signal_rw(float, initial_value=0)

        self.control_channel = derived_signal_rw(
            raw_to_derived=self._get_control_channel,
            set_derived=self._set_control_channel,
            current_channel=self._control_channel,
        )
        super().__init__(
            prefix=prefix,
            num_readback_channel=num_readback_channel,
            heater_setting=heater_setting,
            name=name,
            single_control_channel=single_control_channel,
        )

        self.add_readables(
            [setpoint.user_setpoint for setpoint in self.control_channels.values()]
        )
        self.add_readables(
            list(self.readback.values()), format=StandardReadableFormat.HINTED_SIGNAL
        )

        self.add_readables(
            [
                self._control_channel,
                self.control_channels[control_channel].p,
                self.control_channels[control_channel].i,
                self.control_channels[control_channel].d,
                self.control_channels[control_channel].heater_output_range,
            ],
            StandardReadableFormat.CONFIG_SIGNAL,
        )

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        """
        Set the temperature setpoint for the active control channel.
        """
        high, low = await gather(
            self.temperature_high_limit.get_value(),
            self.temperature_low_limit.get_value(),
        )
        if high >= value >= low:
            await self.control_channels[
                await self.control_channel.get_value()
            ].user_setpoint.set(value)
        else:
            raise ValueError(
                f"{self.name} requested temperature {value} is outside limits: {low}, {high}"
            )

    def _get_control_channel(self, current_channel: int) -> int:
        return current_channel

    async def _set_control_channel(self, value: int) -> None:
        if value < 1 or value > len(self.control_channels):
            raise ValueError(
                f"Control channel must be between 1 and {len(self.control_channels)}."
            )
        await self._control_channel.set(value)
        self._read_config_funcs = (
            self._control_channel.read,
            self.control_channels[value].user_setpoint.read,
            self.control_channels[value].p.read,
            self.control_channels[value].i.read,
            self.control_channels[value].d.read,
            self.control_channels[value].heater_output_range.read,
        )


class Lakeshore336(Lakeshore):
    def __init__(
        self,
        prefix: str,
        control_channel: int = 1,
        name: str = "",
    ):
        """
        Lakeshore 336 temperature controller. With 4 readback and control channels.
        Heater settings are: Off, Low, Medium, High.
        Parameters
        ----------
        prefix : str
            The EPICS prefix for the device.
        control_channel : int, optional
            The initial control channel (default is 1).
        """
        super().__init__(
            prefix=prefix,
            num_readback_channel=4,
            heater_setting=Heater336Settings,
            control_channel=control_channel,
            single_control_channel=False,
            name=name,
        )


class Lakeshore340(Lakeshore):
    def __init__(
        self,
        prefix: str,
        control_channel: int = 1,
        name: str = "",
    ):
        """Lakeshore 340 temperature controller. With 4 readback channels and a single
        control channel.
        Heater settings are in power from 0 to 5. 0 is 0 watt, 5 is 50 watt.

        Parameters
        ----------
        prefix : str
            The EPICS prefix for the device.
        control_channel : int, optional
            The initial control channel (default is 1).
        """

        super().__init__(
            prefix=prefix,
            num_readback_channel=4,
            heater_setting=float,
            control_channel=control_channel,
            single_control_channel=True,
            name=name,
        )
