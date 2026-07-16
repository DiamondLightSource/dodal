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


class BasePID(StandardReadable):
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


class HeaterMode(StrictEnum):
    MANUAL = "Manual"
    AUTO = "Auto"


class HighFieldMagnetTemperatureSensor(BaseTemperatureSensor):
    def __init__(self, prefix: str, suffix: str = "STEMP", name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.temperature = epics_signal_r(float, prefix + suffix)
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.config_readback_2 = epics_signal_r(float, prefix + suffix + "2")
            self.config_readback_3 = epics_signal_r(float, prefix + suffix + "3")

        super().__init__(name=name)


class HighFieldMagnetHeater(BaseHeater):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.setpoint = epics_signal_rw(float, prefix + "MANV:SET")
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.output = epics_signal_r(float, prefix + "HEATERP")
            self.mode = epics_signal_rw(
                HeaterMode,
                read_pv=prefix + "ACTIVITY",
                write_pv=prefix + "ACTIVITY:SET",
            )
        super().__init__(name=name)


class TemperatureController(StandardReadable, StandardMovable):
    def __init__(
        self,
        prefix: str,
        suffix: str,
        sensor: BaseTemperatureSensor,
        heater: BaseHeater,
        pid: BasePID,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.heater = heater
            self.pid = pid
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
