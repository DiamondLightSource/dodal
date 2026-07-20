from __future__ import annotations

import re
from dataclasses import dataclass
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


@dataclass
class TemperatureMovableLogic(MovableWithToleranceLogic):
    async def stop(self):
        current_val = await self.readback.get_value()
        await self.setpoint.set(current_val)


class PID(StandardReadable):
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
    setpoint: SignalRW[float]
    output: SignalR[float]


class BaseTemperatureSensor(StandardReadable, Movable):
    sensor: SignalR[float]

    def __init__(self, name: str = ""):
        self._active_sensor_name: str | None = None
        super().__init__(name=name)

    @property
    def active_sensor(self) -> SignalR[float]:
        if self._active_sensor_name is not None:
            return getattr(self, self._active_sensor_name)
        return self.sensor

    @AsyncStatus.wrap
    async def set(self, value: str) -> None:
        self.set_active_readback(value)

    def set_active_readback(self, sensor_name: str | None) -> None:

        if sensor_name is not None:
            if not re.match(r"^sensor\d*$", sensor_name):
                raise ValueError(
                    f"Invalid readback target '{sensor_name}'. "
                    f"Target must be exactly 'sensor' or 'sensor' followed by an integer (e.g., 'sensor2')."
                )
            if not hasattr(self, sensor_name):
                raise AttributeError(
                    f" '{sensor_name}' is not a valid attribute of {self.__class__.__name__}"
                )
            if not isinstance(getattr(self, sensor_name), SignalR):
                raise TypeError(
                    f"Attribute '{sensor_name}' must be an instance of SignalR, got {type(getattr(self, sensor_name))}"
                )

        self._active_sensor_name = sensor_name


SensorT = TypeVar("SensorT", bound=BaseTemperatureSensor)
HeaterT = TypeVar("HeaterT", bound=BaseHeater)


class TemperatureController(
    StandardReadable, StandardMovable, Generic[SensorT, HeaterT]
):
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

    @property
    def movable_logic(self) -> TemperatureMovableLogic:  # type: ignore[override]
        """Readback needed to be the active sensor, hence not cached_property."""
        return TemperatureMovableLogic(
            setpoint=self.user_setpoint,
            readback=self.sensor.active_sensor,
            tolerance=self.tolerance,
        )
