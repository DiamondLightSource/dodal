from __future__ import annotations

from ophyd_async.core import (
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.temperture_controller import (
    PID,
    BaseHeater,
    BaseTemperatureSensor,
    TemperatureController,
)


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
            self.temperature = epics_signal_r(float, prefix + suffix)

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


class HFMTemperatureController(TemperatureController):
    def __init__(
        self,
        prefix: str,
        suffix: str = "TTEMP:SET",
        config_suffixes: list[str] | None = None,
        name: str = "",
    ):
        sensor = HighFieldMagnetTemperatureSensor(
            prefix=prefix, config_suffixes=config_suffixes
        )
        heater = HighFieldMagnetHeater(prefix=prefix)
        pid = PID(prefix=prefix)
        super().__init__(
            prefix=prefix,
            suffix=suffix,
            sensor=sensor,
            heater=heater,
            pid=pid,
            name=name,
        )
