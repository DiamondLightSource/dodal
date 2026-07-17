from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Generic, TypeVar

from ophyd_async.core import (
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


class BaseTemperatureSensor(StandardReadable):
    temperature: SignalR[float]


SensorT = TypeVar("SensorT", bound=BaseTemperatureSensor)
HeaterT = TypeVar("HeaterT", bound=BaseHeater)


class TemperatureController(
    StandardReadable, StandardMovable, Generic[SensorT, HeaterT]
):
    def __init__(
        self,
        prefix: str,
        suffix: str,
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
            self.user_setpoint = epics_signal_rw(float, prefix + suffix)

        super().__init__(name=name)

    @cached_property
    def movable_logic(self) -> TemperatureMovableLogic:
        return TemperatureMovableLogic(
            setpoint=self.user_setpoint,
            readback=self.sensor.temperature,
            tolerance=self.tolerance,
        )
