"""Base classes and devices for temperature control in Dodal."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cached_property
from typing import Generic, TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    SignalR,
    SignalRW,
    StandardMovable,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.movable import MovableWithToleranceLogic
from dodal.log import LOGGER


@dataclass
class TemperatureMovableLogic(MovableWithToleranceLogic):
    """Movable logic for temperature setpoints with tolerance matching.

    Overrides the default stop behavior to safely halt temperature changes by
    setting the target setpoint to the current readback value.
    """

    async def stop(self):
        """Stop any active temperature move by setting the setpoint to the current readback value."""
        current_val = await self.readback.get_value()
        LOGGER.info(
            f"Stopping temperature move: setting setpoint to current readback value ({current_val})"
        )
        await self.setpoint.set(current_val)


class PID(StandardReadable):
    """PID controller parameters represented as read-write EPICS signals.

    Args:
        prefix: Base EPICS PV prefix for the PID records.
        suffix_p: Suffix for the Proportional gain PV. Defaults to "P".
        suffix_i: Suffix for the Integral gain PV. Defaults to "I".
        suffix_d: Suffix for the Derivative gain PV. Defaults to "D".
        name: Name of the device instance. Defaults to "".
    """

    def __init__(
        self,
        prefix: str,
        suffix_p: str = "P",
        suffix_i: str = "I",
        suffix_d: str = "D",
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.p = epics_signal_rw(float, prefix + suffix_p)
            self.i = epics_signal_rw(float, prefix + suffix_i)
            self.d = epics_signal_rw(float, prefix + suffix_d)
        super().__init__(name=name)


class BaseHeater(StandardReadable):
    """Base interface for a hardware temperature heater unit.

    Attributes:
        setpoint: Signal controlling the heater power setpoint.
        output: Read-only signal indicating current heater output level.
    """

    setpoint: SignalRW[float]
    output: SignalR[float]


class BaseTemperatureSensor(StandardReadable, Movable[str]):
    """Base interface for temperature sensors supporting dynamic readback targeting."""

    sensor: SignalR[float]
    active_sensor: SignalR[float]

    def __init__(self, name: str = ""):

        self._active_sensor_name = soft_signal_rw(str, initial_value="sensor")

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: str) -> None:
        """Select the active sensor channel by name.

        Args:
            value: Attribute name of the target sensor (e.g., 'sensor', 'sensor2').
        """
        await self.set_active_readback(value)

    async def set_active_readback(self, sensor_name: str | None) -> None:
        if sensor_name is not None:
            available = self._get_available_sensors()
            if sensor_name not in available:
                available_sensors = (
                    ", ".join(f"'{s}'" for s in available) if available else "none"
                )
                raise ValueError(
                    f"Invalid readback target '{sensor_name}'. "
                    f"Target must be exactly 'sensor' or 'sensor' followed by an integer (e.g., 'sensor2'). "
                    f"Available sensors on {self.name}: [{available_sensors}]"
                )
            LOGGER.info(f"Setting active sensor on {self.name} to: '{sensor_name}'")
            await self._active_sensor_name.set(sensor_name)
        else:
            LOGGER.info(
                f"Setting active sensor on {self.name} to default: '{sensor_name}'"
            )
            await self._active_sensor_name.set("sensor")

    def _get_available_sensors(self) -> list[str]:
        """Inspect instance attributes for valid sensor signal names.

        Returns:
            Sorted list of attribute names matching the pattern `sensor<int>` that are SignalR instances.
        """
        return sorted(
            [
                attr
                for attr in dir(self)
                if re.match(r"^sensor\d*$", attr)
                and isinstance(getattr(self, attr, None), SignalR)
            ]
        )


SensorT = TypeVar("SensorT", bound=BaseTemperatureSensor)
HeaterT = TypeVar("HeaterT", bound=BaseHeater)


class TemperatureController(
    StandardReadable, StandardMovable[float], Generic[SensorT, HeaterT]
):
    """Temperature controller tying together sensor, heater, and PID units.

    Args:
        setpoint: Signal controlling the user target setpoint.
        sensor: Temperature sensor sub-device instance.
        heater: Heater sub-device instance.
        pid: PID controller sub-device instance.
        name: Name of the controller device instance. Defaults to "".
    """

    def __init__(
        self,
        setpoint: SignalRW[float],
        sensor: SensorT,
        heater: HeaterT,
        pid: PID,
        name: str = "",
    ):

        self.pid = pid
        self.heater = heater
        with self.add_children_as_readables():
            self.sensor = sensor

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.tolerance = soft_signal_rw(float, initial_value=0.1)
            self.user_setpoint = setpoint

        super().__init__(name=name)

    @cached_property
    def movable_logic(self) -> TemperatureMovableLogic:
        """Readback needed to be the active sensor, hence not cached_property."""
        return TemperatureMovableLogic(
            setpoint=self.user_setpoint,
            readback=self.sensor.active_sensor,
            tolerance=self.tolerance,
        )
