"""High-Field Magnet (HFM) temperature controller sub-devices and signals."""

from ophyd_async.core import (
    DeviceVector,
    SignalR,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.temperature_controller import (
    PID,
    BaseHeater,
    TemperatureController,
    TemperatureSensor,
)


class HeaterMode(StrictEnum):
    MANUAL = "Manual"
    AUTO = "Auto"


# class HighFieldMagnetTemperatureSensor(BaseTemperatureSensor):
#     """Temperature sensor sub-device for the High-Field Magnet.

#     Provides three distinct temperature monitoring channels (`sensor`, `sensor2`, `sensor3`)
#     which can be targeted dynamically as the active readback channel.

#     Args:
#         prefix: Base EPICS PV prefix for the sensor records.
#         suffix: Base PV suffix for the primary sensor channel. Defaults to "STEMP".
#         name: Name of the device instance. Defaults to "".
#     """

#     def __init__(
#         self,
#         prefix: str,
#         suffix: str = "STEMP",
#         name: str = "",
#     ):

#         with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
#             self.sensor = epics_signal_r(float, f"{prefix}{suffix}")
#             self.sensor2 = epics_signal_r(float, f"{prefix}{suffix}2")
#             self.sensor3 = epics_signal_r(float, f"{prefix}{suffix}3")
#         super().__init__(name=name)
#         self.active_sensor = derived_signal_r(
#             raw_to_derived=self._select_sensor,
#             active_sensor_name=self._active_sensor_name,
#             sensor=self.sensor,
#             sensor2=self.sensor2,
#             sensor3=self.sensor3,
#         )

#     def _select_sensor(
#         self, active_sensor_name: str, sensor: float, sensor2: float, sensor3: float
#     ) -> float:
#         match active_sensor_name:
#             case "sensor2":
#                 return sensor2
#             case "sensor3":
#                 return sensor3
#             case _:
#                 return sensor


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
    TemperatureController[SignalR[float], HighFieldMagnetHeater]
):
    """Temperature controller for the High-Field Magnet.

    Args:
        prefix: Base EPICS PV prefix for the HFM controller system.
        suffix: PV suffix for the targeted setpoint. Defaults to "TTEMP:SET".
        name: Name of the controller instance. Defaults to "".
    """

    def __init__(
        self,
        prefix: str,
        suffix: str = "TTEMP:SET",
        name: str = "",
    ):
        sensor = TemperatureSensor(
            DeviceVector(
                {
                    1: epics_signal_r(float, f"{prefix}{suffix}"),
                    2: epics_signal_r(float, f"{prefix}{suffix}2"),
                    3: epics_signal_r(float, f"{prefix}{suffix}3"),
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
