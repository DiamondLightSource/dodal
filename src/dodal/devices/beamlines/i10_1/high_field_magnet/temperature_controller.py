from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property

from ophyd_async.core import (
    SignalR,
    SignalRW,
    StandardMovable,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

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


class BaseTemperatureSensor(StandardReadable, ABC):
    @property
    @abstractmethod
    def temperature(self) -> SignalR[float]:
        pass


class HeaterMode(StrictEnum):
    MANUAL = "Manual"
    AUTO = "Auto"


class HighFieldMagnetTemperatureSensor(BaseTemperatureSensor):
    def __init__(
        self,
        prefix: str,
        suffix: str = "STEMP",
        config_suffixes: list[str] | None = None,
        name: str = "",
    ):
        config_suffixes = config_suffixes or ["2", "3"]

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self._temperature = epics_signal_r(float, prefix + suffix)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            for sfx in config_suffixes:
                signal_name = f"config_{sfx}"
                if hasattr(self, signal_name):
                    raise AttributeError(
                        f"Cannot add configuration signal '{signal_name}': attribute already exists."
                    )
                signal = epics_signal_r(float, prefix + suffix + sfx)
                setattr(self, signal_name, signal)
        super().__init__(name=name)

    @property
    def temperature(self) -> SignalR[float]:
        return self._temperature


class HighFieldMagnetHeater(BaseHeater):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.mode = epics_signal_rw(
                HeaterMode,
                read_pv=prefix + "ACTIVITY",
                write_pv=prefix + "ACTIVITY:SET",
            )
            self.setpoint = epics_signal_rw(float, prefix + "MANV:SET")
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.output = epics_signal_r(float, prefix + "HEATERP")

        super().__init__(name=name)


class TemperatureController(StandardReadable, StandardMovable):
    def __init__(
        self,
        prefix: str,
        suffix: str,
        sensor: BaseTemperatureSensor,
        heater: BaseHeater,
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

    @classmethod
    def from_prefix(
        cls,
        prefix: str,
        suffix: str = "TTEMP:SET",
        config_suffixes: list[str] | None = None,
        name: str = "",
    ) -> TemperatureController:
        """Helper factory to instantiate the entire stack from a single prefix."""
        sensor = HighFieldMagnetTemperatureSensor(
            prefix=prefix, config_suffixes=config_suffixes
        )
        heater = HighFieldMagnetHeater(prefix=prefix)
        pid = PID(prefix=prefix)
        return cls(
            prefix=prefix,
            suffix=suffix,
            sensor=sensor,
            heater=heater,
            pid=pid,
            name=name,
        )
