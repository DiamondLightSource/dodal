"""Cryocon M32 temperature sensor, heater, and controller devices."""

from ophyd_async.core import (
    DeviceMap,
    SignalRW,
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


def epics_signal_dmd_sts(
    datatype: type, prefix: str, infix: str, suffix: str
) -> SignalRW:
    """Helper to create an epics_signal_rw with DMD and STS paths."""
    return epics_signal_rw(
        datatype,
        write_pv=f"{prefix}DMD:{infix}{suffix}",
        read_pv=f"{prefix}STS:{infix}{suffix}",
    )


class HeaterRange(StrictEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class HeaterMode(StrictEnum):
    OFF = "Off"
    PID = "PID"
    MANUAL = "Man"
    TABLE = "Table"
    RAMP = "RampP"


class CryoconM32Sensor(BaseTemperatureSensor):
    """Configuration signal group for a Cryocon M32 sensor channel.

    Attributes:
        min: Minimum valid sensor temperature reading.
        max: Maximum valid sensor temperature reading.
        slope: Temperature slope.
        offset: Temperature offset value.

    Args:
        prefix: Base EPICS PV prefix including status path and sensor channel (e.g. "PREFIX:STS:T1:").
        name: Name of the configuration block instance. Defaults to "".
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.min = epics_signal_r(float, prefix + ":MIN")
            self.max = epics_signal_r(float, prefix + ":MAX")
            self.slope = epics_signal_r(float, prefix + ":SLOPE")
            self.offset = epics_signal_r(float, prefix + ":OFFSET")
        super().__init__(pv=prefix, name=name)


class CryoconM32Heater(BaseHeater):
    """Cryocon M32 heater.

    Attributes:
        setpoint: Manual output signal.
        output_range: Heater power range setting (Low, Medium, High).
        mode: Active control mode setting (Off, PID, Manual, Table, Ramp).
        output: Current heater power readback signal.

    Args:
        prefix: Base EPICS PV prefix for the heater unit.
        infix: Loop/channel infix (e.g. "LOOP1:").
        name: Name of the heater. Defaults to "".
    """

    def __init__(self, prefix: str, infix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.setpoint = epics_signal_dmd_sts(float, prefix, infix, "MANUAL")
            self.output_range = epics_signal_dmd_sts(
                HeaterRange, prefix, infix, "RANGE"
            )
            self.mode = epics_signal_rw(HeaterMode, f"{prefix}DMD:{infix}LOOPTYPE")

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.output = epics_signal_r(float, f"{prefix}STS:{infix}HTRREAD")

        super().__init__(name=name)


class SuperConductingMagnetTemperatureController(
    TemperatureController[CryoconM32Sensor, CryoconM32Heater]
):
    """Super Conducting Magnet (SCM) Cryocon M32 temperature controller.

    Args:
        prefix: Base EPICS PV prefix for the temperature controller.
        infix: Controller loop channel infix. Defaults to "LOOP1:".
        name: Name of the controller instance. Defaults to "".
    """

    def __init__(
        self,
        prefix: str,
        infix: str = "LOOP1:",
        name: str = "",
    ):
        sensor = TemperatureSensor[CryoconM32Sensor](
            DeviceMap(
                {
                    "sensor1": CryoconM32Sensor(prefix + "STS:T1"),
                    "sensor2": CryoconM32Sensor(prefix + "STS:T2"),
                }
            )
        )
        heater = CryoconM32Heater(prefix=prefix, infix=infix)
        setpoint = epics_signal_dmd_sts(float, prefix, infix, "SETPOINT")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.ramp_mode = epics_signal_r(str, f"{prefix}STS:{infix}LOOPRAMP")
            self.ramp_rate = epics_signal_dmd_sts(float, prefix, infix, "RAMPRATE")
        pid = PID(
            prefix=f"{prefix}DMD:{infix}",
            suffix_p="PGAIN",
            suffix_i="IGAIN",
            suffix_d="DGAIN",
        )
        super().__init__(
            setpoint=setpoint,
            sensor=sensor,
            heater=heater,
            pid=pid,
            name=name,
        )
