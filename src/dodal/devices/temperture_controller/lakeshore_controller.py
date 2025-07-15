from bluesky.protocols import Movable, Reading
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    soft_signal_rw,
)

from .pid_io import PIDBaseIO
from .temperature_io import LakeshoreBaseIO


class Lakeshore336(StrictEnum):
    """These are the sensitivity setting for Femto 3xx current amplifier"""

    OFF = "Off"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Lakeshore(StandardReadable, Movable):
    """
    Lakeshore temperature controller that combines PID control and temperature reading.
    This class inherits from PIDBaseIO for PID control and TemperatureBaseIO for temperature
    reading functionalities.
    """

    def __init__(
        self,
        prefix: str,
        no_channels: int,
        heater_table: type[StrictEnum],
        control_channels: int = 1,
        name: str = "",
    ):
        self.temperature = LakeshoreBaseIO(
            prefix=prefix,
            no_channels=no_channels,
            heater_table=heater_table,
            name=name,
        )
        self.add_readables(
            list(self.temperature.setpoint.values())
            + list(self.temperature.readback.values())
        )
        self.PID = PIDBaseIO(prefix=prefix, no_channels=no_channels, name=name)
        self.control_channels = soft_signal_rw(int, initial_value=control_channels)
        self.set_control_channels(control_channels)

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        """
        Set the temperature setpoint for all channels.
        This method overrides the Movable interface's set method.
        """

        await self.temperature.setpoint[await self.control_channels.get_value()].set(
            value
        )

    async def read(self) -> dict[str, Reading]:
        return await super().read()

    def set_control_channels(self, value: int) -> None:
        """
        Set the number of control channels.
        This method allows dynamic adjustment of the number of control channels.
        """
        if value < 1 or value > len(self.PID.p):
            raise ValueError(
                f"Control channels must be between 1 and {len(self.PID.p)}."
            )
        self.control_channels.set(value)
        self._read_config_funcs = ()
        self._has_hints = ()
        self.add_readables(
            [
                self.control_channels,
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
