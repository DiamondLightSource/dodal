from ophyd_async.core import (
    EnabledDisabled,
    InOut,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw,
    epics_signal_x,
)


class CryoStream(StandardReadable):
    MAX_TEMP_K = 110
    MAX_PRESSURE_BAR = 0.1

    def __init__(self, prefix: str, name: str = ""):
        self.course = epics_signal_rw(InOut, f"{prefix}-EA-CJET-01:COARSE:CTRL")
        self.fine = epics_signal_rw(InOut, f"{prefix}-EA-CJET-01:FINE:CTRL")
        self.temperature_k = epics_signal_r(float, f"{prefix}-EA-CSTRM-01:TEMP")
        self.back_pressure_bar = epics_signal_r(
            float, f"{prefix}-EA-CSTRM-01:BACKPRESS"
        )
        super().__init__(name)


class TurboEnum(StrictEnum):
    OFF = "Off"
    ON = "On"
    AUTO = "Auto"


class OxfordCryoStreamController(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Any signals that should be read once at the start of the scan
            self.turbo = epics_signal_rw(str, f"{prefix}TURBO")
            self.turbo_mode = epics_signal_rw(TurboEnum, f"{prefix}TURBOMODE")

            self.serial_comms = epics_signal_rw(EnabledDisabled, f"{prefix}DISABLE")
            self.status = epics_signal_r(str, f"{prefix}STATUS.SEVR")

        with self.add_children_as_readables():
            # Any signals that should be read at every point in the scan

            self.purge = epics_signal_x(f"{prefix}PURGE.PROC")
            self.hold = epics_signal_x(f"{prefix}HOLD.PROC")
            self.start = epics_signal_x(f"{prefix}RESTART.PROC")
            self.pause = epics_signal_x(f"{prefix}PAUSE.PROC")
            self.resume = epics_signal_x(f"{prefix}RESUME.PROC")
            self.end = epics_signal_x(f"{prefix}END.PROC")
            self.stop = epics_signal_x(f"{prefix}STOP.PROC")

            self.ramp_rate = epics_signal_rw(float, f"{prefix}RRATE")
            self.ramp_temp = epics_signal_rw(float, f"{prefix}RTEMP")
            self.ramp = epics_signal_x(f"{prefix}RAMP.PROC")

            self.plat_time = epics_signal_rw(float, f"{prefix}PTIME")
            self.plat = epics_signal_x(f"{prefix}PLAT.PROC")

            self.cool_temp = epics_signal_rw(float, f"{prefix}CTEMP")
            self.cool = epics_signal_x(f"{prefix}COOL.PROC")

            self.end_rate = epics_signal_rw(float, f"{prefix}ERATE")

        super().__init__(name)


class OxfordCryoStreamStatus(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Any signals that should be read once at the start of the scan

            self.pump_uptime = epics_signal_r(float, f"{prefix}RUNTIME")
            self.controller_number = epics_signal_r(float, f"{prefix}CTRLNUM")
            self.software_version = epics_signal_r(float, f"{prefix}VER")
            self.evap_adjust = epics_signal_r(float, f"{prefix}EVAPADJUST")
            self.series = epics_signal_r(str, f"{prefix}SERIES")

        with self.add_children_as_readables():
            # Any signals that should be read at every point in the scan
            self.setpoint = epics_signal_r(float, f"{prefix}SETPOINT")
            self.temp = epics_signal_r(float, f"{prefix}TEMP")
            self.error = epics_signal_r(float, f"{prefix}ERROR")
            self.mode = epics_signal_r(str, f"{prefix}RUNMODE")
            self.phase = epics_signal_r(str, f"{prefix}PHASE")
            self.ramp_rate_setpoint = epics_signal_r(float, f"{prefix}RAMPRATE")
            self.target_temp = epics_signal_r(float, f"{prefix}TARGETTEMP")
            self.evap_temp = epics_signal_r(float, f"{prefix}EVAPTEMP")
            self.time_remaining = epics_signal_r(float, f"{prefix}REMAINING")
            self.gas_flow = epics_signal_r(float, f"{prefix}GASFLOW")
            self.gas_heat = epics_signal_r(float, f"{prefix}GASHEAT")
            self.evap_heat = epics_signal_r(float, f"{prefix}EVAPHEAT")
            self.suct_temp = epics_signal_r(float, f"{prefix}SUCTTEMP")
            self.suct_heat = epics_signal_r(float, f"{prefix}SUCTHEAT")
            self.back_pressure = epics_signal_r(float, f"{prefix}BACKPRESS")

        super().__init__(name)


class OxfordCryoStream(StandardReadable):
    def __init__(self, prefix: str, name=""):
        with self.add_children_as_readables():
            self.controller = OxfordCryoStreamController(prefix=prefix)
            self.status = OxfordCryoStreamStatus(prefix=prefix)

        super().__init__(name)
