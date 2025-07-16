from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_rw,
    soft_signal_rw,
)

from .pid_io import PID_INPUT_CHANNEL, Lakeshore336_PID_MODE, PIDBaseIO
from .temperature_io import LakeshoreBaseIO


class Lakeshore(StandardReadable, Movable):
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
    heater_table : type[StrictEnum]
        Enum type for heater settings.
    control_channel : int, optional
        The initial control channel (default is 1).
    name : str, optional
        Name of the device.

    Attributes
    ----------
    temperature : LakeshoreBaseIO
        Temperature IO interface.
    PID : PIDBaseIO
        PID IO interface.
    control_channel : derived_signal_rw
        Signal for selecting the control channel.

    Methods
    -------
    set(value: float)
        Set the temperature setpoint for the selected control channel.
    """

    def __init__(
        self,
        prefix: str,
        no_channels: int,
        heater_table: type[StrictEnum],
        mode_table: type[StrictEnum] = Lakeshore336_PID_MODE,
        input_channel_table: type[StrictEnum] = PID_INPUT_CHANNEL,
        control_channel: int = 1,
        name: str = "",
    ):
        self.temperature = LakeshoreBaseIO(
            prefix=prefix,
            no_channels=no_channels,
            heater_setting=heater_table,
            name=name,
        )

        self.PID = PIDBaseIO(
            prefix=prefix,
            no_channels=no_channels,
            mode_table=mode_table,
            input_channel_table=input_channel_table,
            name=name,
        )
        self._control_channel = soft_signal_rw(int, initial_value=control_channel)
        self.add_readables(
            list(self.temperature.setpoint.values())
            + list(self.temperature.readback.values())
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
        Set the temperature setpoint for all channels.
        This method overrides the Movable interface's set method.
        """

        await self.temperature.setpoint[await self.control_channel.get_value()].set(
            value
        )

    def _get_control_channel(self, current_channel: int) -> int:
        return current_channel

    async def _set_control_channel(self, value: int) -> None:
        """
        Set the number of control channels.
        This method allows dynamic adjustment of the number of control channels.
        """
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
            [self.temperature.readback[value], self.temperature.setpoint[value]],
            StandardReadableFormat.HINTED_SIGNAL,
        )
