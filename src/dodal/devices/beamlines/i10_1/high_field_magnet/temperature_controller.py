"""High-Field Magnet (HFM) temperature controller sub-devices and signals."""

from ophyd_async.core import (
    DeviceMap,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.temperature_controller import (
    PID,
    BaseHeater,
    BaseTemperatureSensor,
    TemperatureController,
    TemperatureSensor,
)


class HeaterMode(StrictEnum):
    MANUAL = "Manual"
    AUTO = "Auto"


class HighFieldMagnetSensor(BaseTemperatureSensor):
    """Single channel temperature sensor sub-device for High-Field Magnet."""

    def __init__(self, pv: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.sensor = epics_signal_r(float, pv)
        super().__init__(name=name)

    def set_name(self, name: str, *, child_name_separator: str | None = None) -> None:
        super().set_name(name, child_name_separator=child_name_separator)
        self.sensor.set_name(name=name)


class HighFieldMagnetHeater(BaseHeater):
    """Heater unit for the High-Field Magnet.

    Attributes:
        mode: Signal controlling heater mode selection (Manual vs Auto).
        setpoint: Signal controlling manual output power/setpoint.
        output: Readback signal for current heater power.

    Args:
        prefix: Base EPICS PV prefix for heater control records.
        name: Name of the device instance. Defaults to "".
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.mode = epics_signal_rw(
                HeaterMode,
                read_pv=f"{prefix}ACTIVITY",
                write_pv=f"{prefix}ACTIVITY:SET",
            )
            self.setpoint = epics_signal_rw(float, f"{prefix}MANV:SET")
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.output = epics_signal_r(float, f"{prefix}HEATERP")

        super().__init__(name=name)


class HighFieldMagnetTemperatureController(
    TemperatureController[HighFieldMagnetSensor, HighFieldMagnetHeater]
):
    """Temperature controller for the High-Field Magnet.

    Args:
        prefix: Base EPICS PV prefix for the HFM controller system.
        suffix: PV suffix for the targeted setpoint. Defaults to "TTEMP:SET".
        sensor_map: Mapping of sensor names to PV suffix strings for the underlying
            :class:`~ophyd_async.core.DeviceMap`. If ``None``, defaults to
            ``{"sensor1": "", "sensor2": "2", "sensor3": "3"}``.
        name: Name of the controller instance. Defaults to "".
    """

    def __init__(
        self,
        prefix: str,
        suffix: str = "TTEMP:SET",
        sensor_map: dict[str, str] | None = None,
        name: str = "",
    ):
        if sensor_map is None:
            sensor_map = {"sensor1": ""}
            sensor_map.update({f"sensor{i}": str(i) for i in range(2, 4)})
        sensor = TemperatureSensor[HighFieldMagnetSensor](
            DeviceMap(
                {
                    name_key: HighFieldMagnetSensor(f"{prefix}STEMP{pv_suffix}")
                    for name_key, pv_suffix in sensor_map.items()
                }
            )
        )
        heater = HighFieldMagnetHeater(prefix=prefix)
        setpoint = epics_signal_rw(float, f"{prefix}{suffix}")
        pid = PID(prefix=prefix)
        super().__init__(
            setpoint=setpoint,
            sensor=sensor,
            heater=heater,
            pid=pid,
            name=name,
        )
