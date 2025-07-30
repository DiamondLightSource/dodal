from asyncio import gather

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    SignalDatatypeT,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_rw,
    soft_signal_rw,
)

from .lakeshore_io import (
    LakeshoreBaseIO,
    PIDBaseIO,
)


class Lakeshore(StandardReadable, Movable[float]):
    """
    Lakeshore temperature controller device.

    This class provides an interface for controlling and reading from a Lakeshore temperature controller.
    It supports multiple channels and PID control.

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
        no_channels: int,
        heater_setting: type[SignalDatatypeT],
        control_channel: int = 1,
        single_control_channel: bool = False,
        name: str = "",
    ):
        self.temperature = LakeshoreBaseIO(
            prefix=prefix,
            no_channels=no_channels,
            heater_setting=heater_setting,
            single_control_channel=single_control_channel,
            name=name,
        )

        self.PID = PIDBaseIO(
            prefix=prefix,
            no_channels=no_channels,
            single_control_channel=single_control_channel,
            name=name,
        )
        self._control_channel = soft_signal_rw(int, initial_value=control_channel)
        self.temperature_high_limit = soft_signal_rw(float, initial_value=400)
        self.temperature_low_limit = soft_signal_rw(float, initial_value=0)

        self.add_readables(
            list(self.temperature.user_setpoint.values())
            + list(self.temperature.user_readback.values())
        )

        self.add_readables(
            [
                self._control_channel,
                self.PID.p[control_channel],
                self.PID.i[control_channel],
                self.PID.d[control_channel],
            ],
            StandardReadableFormat.CONFIG_SIGNAL,
        )

        self.control_channel = derived_signal_rw(
            raw_to_derived=self._get_control_channel,
            set_derived=self._set_control_channel,
            current_channel=self._control_channel,
        )

        super().__init__(name=name)

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
            await self.temperature.user_setpoint[
                await self.control_channel.get_value()
            ].set(value)
        else:
            raise ValueError(f"Requested temperature must be withing {high} and {low}")

    def _get_control_channel(self, current_channel: int) -> int:
        return current_channel

    async def _set_control_channel(
        self, value: int, readback: int | None = None
    ) -> None:
        readback = readback if readback else value
        if value < 1 or value > len(self.PID.p):
            raise ValueError(
                f"Control channels must be between 1 and {len(self.PID.p)}."
            )
        await self._control_channel.set(value)
        self._read_config_funcs = ()
        self._has_hints = ()
        self.add_readables(
            [
                self._control_channel,
                self.PID.p[value],
                self.PID.i[value],
                self.PID.d[value],
            ],
            StandardReadableFormat.CONFIG_SIGNAL,
        )

        self.add_readables(
            [
                self.temperature.user_readback[readback],
                self.temperature.user_setpoint[value],
            ],
            StandardReadableFormat.HINTED_SIGNAL,
        )
