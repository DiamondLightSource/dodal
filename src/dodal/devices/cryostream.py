from ophyd_async.core import (
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


class TurboEnum(StrictEnum):
    OFF = "Off"
    ON = "On"
    AUTO = "Auto"


class CryoStreamSelection(StrictEnum):
    CRYOJET = "CryoJet"
    HC1 = "HC1"


class OxfordCryoStream(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.temp = epics_signal_r(float, f"{prefix}TEMP")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Any signals that should be read once at the start of the scan

            self.turbo = epics_signal_rw(str, f"{prefix}TURBO")
            self.turbo_mode = epics_signal_rw(TurboEnum, f"{prefix}TURBOMODE")
            self.status = epics_signal_r(str, f"{prefix}STATUS.SEVR")
            self.pump_uptime = epics_signal_r(float, f"{prefix}RUNTIME")
            self.controller_number = epics_signal_r(float, f"{prefix}CTRLNUM")
            self.software_version = epics_signal_r(float, f"{prefix}VER")
            self.evap_adjust = epics_signal_r(float, f"{prefix}EVAPADJUST")
            self.series = epics_signal_r(str, f"{prefix}SERIES")
            self.error = epics_signal_r(float, f"{prefix}ERROR")
            self.mode = epics_signal_r(str, f"{prefix}RUNMODE")

        with self.add_children_as_readables():
            # Any signals that should be read at every point in the scan
            self.ramp_rate = epics_signal_rw(float, f"{prefix}RRATE")
            self.ramp_temp = epics_signal_rw(float, f"{prefix}RTEMP")
            self.plat_time = epics_signal_rw(float, f"{prefix}PTIME")
            self.cool_temp = epics_signal_rw(float, f"{prefix}CTEMP")
            self.end_rate = epics_signal_rw(float, f"{prefix}ERATE")
            self.setpoint = epics_signal_r(float, f"{prefix}SETPOINT")
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

        self.purge = epics_signal_x(f"{prefix}PURGE.PROC")
        self.hold = epics_signal_x(f"{prefix}HOLD.PROC")
        self.start = epics_signal_x(f"{prefix}RESTART.PROC")
        self.pause = epics_signal_x(f"{prefix}PAUSE.PROC")
        self.resume = epics_signal_x(f"{prefix}RESUME.PROC")
        self.end = epics_signal_x(f"{prefix}END.PROC")
        self.stop = epics_signal_x(f"{prefix}STOP.PROC")
        self.plat = epics_signal_x(f"{prefix}PLAT.PROC")
        self.cool = epics_signal_x(f"{prefix}COOL.PROC")
        self.ramp = epics_signal_x(f"{prefix}RAMP.PROC")

        super().__init__(name)


class OxfordCryoJet(StandardReadable):
    # TODO: https://github.com/DiamondLightSource/dodal/issues/1486
    # This is a placeholder implementation to get it working with I03, the actual cryojet has many more PVs
    def __init__(self, prefix: str, name=""):
        with self.add_children_as_readables():
            self.coarse = epics_signal_rw(InOut, f"{prefix}COARSE:CTRL")
            self.fine = epics_signal_rw(InOut, f"{prefix}FINE:CTRL")

        super().__init__(name)


class CryoStreamGantry(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.cryostream_selector = epics_signal_r(
                CryoStreamSelection, f"{prefix}-EA-GANT-01:CTRL"
            )
            self.hc1_selected = epics_signal_r(
                int, f"{prefix}-MO-STEP-02:GPIO_INP_BITS.B2"
            )
            self.cryostream_selected = epics_signal_r(
                int, f"{prefix}-MO-STEP-02:GPIO_INP_BITS.B3"
            )
        super().__init__(name)
