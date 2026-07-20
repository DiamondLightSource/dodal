from ophyd_async.core import (
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
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.sensor = epics_signal_r(float, prefix + "STS:T1")
            self.sensor2 = epics_signal_r(float, prefix + "STS:T2")
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self._create_config_signals(prefix=prefix + "STS:T1", attr_prefix="sensor")
            self._create_config_signals(prefix=prefix + "STS:T2", attr_prefix="sensor2")

        super().__init__(name=name)

    def _create_config_signals(self, prefix: str, attr_prefix: str) -> None:
        """Helper to dynamically generate flat configuration attributes."""
        suffixes = ["MIN", "MAX", "SLOPE", "OFFSET"]
        for sfx in suffixes:
            attr_name = f"{attr_prefix}_{sfx.lower()}"
            signal = epics_signal_r(float, f"{prefix}:{sfx}")
            setattr(self, attr_name, signal)


class CryoconM32Heater(BaseHeater):
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


class SCMTemperatureController(TemperatureController):
    def __init__(
        self,
        prefix: str,
        infix: str = "LOOP1:",
        name: str = "",
    ):

        sensor = CryoconM32Sensor(prefix=prefix)
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
