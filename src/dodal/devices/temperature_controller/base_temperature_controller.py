from __future__ import annotations

from abc import ABC, abstractmethod
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


class BaseTemperatureSensor(StandardReadable, ABC, Movable):
    @property
    @abstractmethod
    def temperature(self) -> SignalR[float]:
        pass

    def __init__(self, name: str = ""):
        self._active_attr_name: str | None = None

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self._auto_temp = self.temperature

        super().__init__(name=name)

    @property
    def active_sensor(self) -> SignalR[float]:
        if self._active_attr_name is not None:
            return getattr(self, self._active_attr_name)
        return self.temperature

    @AsyncStatus.wrap
    async def set(self, value: str) -> None:
        self.set_active_readback(value)

    def set_active_readback(self, attr_name: str | None) -> None:

        if attr_name is not None:
            if not hasattr(self, attr_name):
                raise AttributeError(
                    f" '{attr_name}' is not a valid attribute of {self.__class__.__name__}"
                )
            if not isinstance(getattr(self, attr_name), SignalR):
                raise TypeError(
                    f"Attribute '{attr_name}' must be an instance of SignalR, got {type(getattr(self, attr_name))}"
                )

        self._active_attr_name = attr_name


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

    @cached_property
    def movable_logic(self) -> TemperatureMovableLogic:
        return TemperatureMovableLogic(
            setpoint=self.user_setpoint,
            readback=self.sensor.active_sensor,
            tolerance=self.tolerance,
        )
