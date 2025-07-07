from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class InOut(StrictEnum):
    IN = "In"
    OUT = "Out"


class CryoStream(StandardReadable):
    """This is an i03 specific device"""

    def __init__(self, prefix: str, name: str = ""):
        self.course = epics_signal_rw(InOut, f"{prefix}-EA-CJET-01:COARSE:CTRL")
        self.fine = epics_signal_rw(InOut, f"{prefix}-EA-CJET-01:FINE:CTRL")
        self.temperature_k = epics_signal_r(float, f"{prefix}-EA-CSTRM-01:TEMP")
        self.back_pressure_bar = epics_signal_r(
            float, f"{prefix}-EA-CSTRM-01:BACKPRESS"
        )

        super().__init__(name)


class OxfordCryoStreamController(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        self.purge = epics_signal_rw(float, f"{prefix}PURGE")
        self.dsdsd = epics_signal_rw(float, f"{prefix}dfdf")

        super().__init__(name)


class OxfordCryoStreamStatus(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        self.setpoint = epics_signal_r(float, f"{prefix}SETPOINT")
        self.temp = epics_signal_r(float, f"{prefix}TEMP")
        self.error = epics_signal_r(float, f"{prefix}ERROR")
        self.mode = epics_signal_r(str, f"{prefix}RUNMODE")
        self.phase = epics_signal_r(str, f"{prefix}PHASE")
        self.ramp_rate = epics_signal_r(float, f"{prefix}RAMPRATE")
        self.target_temp = epics_signal_r(float, f"{prefix}TARGETTEMP")
        self.evap_temp = epics_signal_r(float, f"{prefix}EVAPTEMP")
        self.time_remaining = epics_signal_r(float, f"{prefix}REMAINING")
        self.gas_flow = epics_signal_r(float, f"{prefix}GASFLOW")
        self.gas_heat = epics_signal_r(float, f"{prefix}GASHEAT")
        self.evap_heat = epics_signal_r(float, f"{prefix}EVAPHEAT")
        self.suct_temp = epics_signal_r(float, f"{prefix}SUCTTEMP")
        self.suct_heat = epics_signal_r(float, f"{prefix}SUCTHEAT")
        self.back_pressure = epics_signal_r(float, f"{prefix}BACKPRESS")

        self.pump_uptime = epics_signal_r(float, f"{prefix}RUNTIME")
        self.controller_number = epics_signal_r(float, f"{prefix}CTRLNUM")
        self.software_version = epics_signal_r(float, f"{prefix}VER")
        self.evap_adjust = epics_signal_r(float, f"{prefix}EVAPADJUST")

        super().__init__(name)


class OxfordCryoStream(StandardReadable):
    def __init__(self, prefix: str, name=""):
        self.controller = OxfordCryoStreamController(prefix=prefix)
        self.status = OxfordCryoStreamStatus(prefix=prefix)

        super().__init__(name)
