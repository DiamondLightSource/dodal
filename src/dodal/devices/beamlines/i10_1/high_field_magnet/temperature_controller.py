"""High-Field Magnet (HFM) temperature controller sub-devices and signals."""

from ophyd_async.core import StandardReadableFormat, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.temperature_controller import (
    PID,
    BaseHeater,
    BaseTemperatureSensor,
    TemperatureController,
)


class HeaterMode(StrictEnum):
    MANUAL = "Manual"
    AUTO = "Auto"


class HighFieldMagnetTemperatureSensor(BaseTemperatureSensor):
    """Temperature sensor sub-device for the High-Field Magnet.

    Provides three distinct temperature monitoring channels (`sensor`, `sensor2`, `sensor3`)
    which can be targeted dynamically as the active readback channel.

    Args:
        prefix: Base EPICS PV prefix for the sensor records.
        suffix: Base PV suffix for the primary sensor channel. Defaults to "STEMP".
        name: Name of the device instance. Defaults to "".
    """

    def __init__(
        self,
        prefix: str,
        suffix: str = "STEMP",
        name: str = "",
    ):

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.sensor = epics_signal_r(float, prefix + suffix)
            self.sensor2 = epics_signal_r(float, prefix + suffix + "2")
            self.sensor3 = epics_signal_r(float, prefix + suffix + "3")
        super().__init__(name=name)


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
                read_pv=prefix + "ACTIVITY",
                write_pv=prefix + "ACTIVITY:SET",
            )
            self.setpoint = epics_signal_rw(float, prefix + "MANV:SET")
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.output = epics_signal_r(float, prefix + "HEATERP")

        super().__init__(name=name)


class HFMTemperatureController(TemperatureController):
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
        sensor = HighFieldMagnetTemperatureSensor(prefix=prefix)
        heater = HighFieldMagnetHeater(prefix=prefix)
        setpoint = epics_signal_rw(float, prefix + suffix)
        pid = PID(prefix=prefix)
        super().__init__(
            setpoint=setpoint,
            sensor=sensor,
            heater=heater,
            pid=pid,
            name=name,
        )
