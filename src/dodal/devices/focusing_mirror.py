import time
from enum import Enum

from ophyd import Component, Device, EpicsMotor, EpicsSignal, Signal
from ophyd.status import Status

from dodal.log import LOGGER

VOLTAGE_POLLING_DELAY_S = 0.5

# The default timeout is 60 seconds as voltage slew rate is typically ~2V/s
DEFAULT_SETTLE_TIME_S = 60

DEMAND_ACCEPTED_OK = 1


class MirrorStripe(Enum):
    RHODIUM = "Rhodium"
    BARE = "Bare"
    PLATINUM = "Platinum"


class MirrorVoltageSignal(Signal):
    def set(self, value, *, timeout=None, settle_time=0, **kwargs):
        actual_v: EpicsSignal = None
        demand_accepted_v: EpicsSignal = None
        actual_v, setpoint_v, demand_accepted_v = self.parent.components_for_channel(
            self.attr_name
        )

        LOGGER.debug(f"setting {setpoint_v.name} to {value}")
        setpoint_status = setpoint_v.set(value)
        demand_accepted_status = Status(self, DEFAULT_SETTLE_TIME_S)

        def demand_check_callback(expiry_time_s):
            accepted = demand_accepted_v.get()
            if accepted == DEMAND_ACCEPTED_OK:
                LOGGER.debug(f"Demand accepted for {setpoint_v.name}")
                demand_accepted_status.set_finished()
            elif time.time() < expiry_time_s:
                check_timer = Status(self, VOLTAGE_POLLING_DELAY_S)
                check_timer.add_callback(lambda _: demand_check_callback(expiry_time_s))
            # else timeout handled by parent demand_accepted_status

        def setpoint_callback(status: Status):
            if status.success:
                try:
                    accepted = demand_accepted_v.get()
                    if accepted == DEMAND_ACCEPTED_OK:
                        LOGGER.debug(f"Demand accepted for {setpoint_v.name}")
                        demand_accepted_status.set_finished()
                    else:
                        expiry_time_s = time.time() + DEFAULT_SETTLE_TIME_S
                        check_timer = Status(self, VOLTAGE_POLLING_DELAY_S)
                        check_timer.add_callback(
                            lambda _: demand_check_callback(expiry_time_s)
                        )
                except Exception as e:
                    LOGGER.warn(
                        f"Failed to fetch {setpoint_v.name} Demand Accepted", exc_info=e
                    )
                    demand_accepted_status.set_exception(e)

        setpoint_status.add_callback(setpoint_callback)
        status = setpoint_status & demand_accepted_status
        return status


class VFMMirrorVoltages(Device):
    _channel14_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V14R")
    _channel14_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V14D")
    _channel14_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V14DSEV")
    _channel15_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V15R")
    _channel15_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V15D")
    _channel15_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V15DSEV")
    _channel16_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V16R")
    _channel16_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V16D")
    _channel16_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V16DSEV")
    _channel17_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V17R")
    _channel17_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V17D")
    _channel17_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V17DSEV")
    _channel18_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V18R")
    _channel18_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V18D")
    _channel18_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V18DSEV")
    _channel19_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V19R")
    _channel19_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V19D")
    _channel19_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V19DSEV")
    _channel20_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V20R")
    _channel20_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V20D")
    _channel20_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V20DSEV")
    _channel21_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V21R")
    _channel21_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V21D")
    _channel21_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V21DSEV")

    channel14 = Component(MirrorVoltageSignal)
    channel15 = Component(MirrorVoltageSignal)
    channel16 = Component(MirrorVoltageSignal)
    channel17 = Component(MirrorVoltageSignal)
    channel18 = Component(MirrorVoltageSignal)
    channel19 = Component(MirrorVoltageSignal)
    channel20 = Component(MirrorVoltageSignal)
    channel21 = Component(MirrorVoltageSignal)

    voltage_lookup_table_path: str = (
        "/dls_sw/i03/software/daq_configuration/json/mirrorFocus.json"
    )

    def components_for_channel(
        self, name
    ) -> tuple[EpicsSignal, EpicsSignal, EpicsSignal]:
        return (
            getattr(self, f"_{name}_actual_v"),
            getattr(self, f"_{name}_setpoint_v"),
            getattr(self, f"_{name}_demand_accepted"),
        )

    @property
    def voltage_channels(self) -> list[MirrorVoltageSignal]:
        return [
            getattr(self, name)
            for name in [
                "channel14",
                "channel15",
                "channel16",
                "channel17",
                "channel18",
                "channel19",
                "channel20",
                "channel21",
            ]
        ]


class FocusingMirror(Device):
    """Focusing Mirror"""

    yaw_mrad: EpicsMotor = Component(EpicsMotor, "YAW")
    pitch_mrad: EpicsMotor = Component(EpicsMotor, "PITCH")
    fine_pitch_mm: EpicsMotor = Component(EpicsMotor, "FPMTR")
    roll_mrad: EpicsMotor = Component(EpicsMotor, "ROLL")
    vert_mm: EpicsMotor = Component(EpicsMotor, "VERT")
    lat_mm: EpicsMotor = Component(EpicsMotor, "LAT")
    jack1_mm: EpicsMotor = Component(EpicsMotor, "Y1")
    jack2_mm: EpicsMotor = Component(EpicsMotor, "Y2")
    jack3_mm: EpicsMotor = Component(EpicsMotor, "Y3")
    translation1_mm: EpicsMotor = Component(EpicsMotor, "X1")
    translation2_mm: EpicsMotor = Component(EpicsMotor, "X2")

    stripe: EpicsSignal = Component(EpicsSignal, "STRP:DVAL", string=True)
    # apply the current set stripe setting
    apply_stripe: EpicsSignal = Component(EpicsSignal, "CHANGE.PROC")

    bragg_to_lat_lookup_table_path: str = (
        "CONFIGURE_ME"  # configured in per-mirror beamline-specific setup
    )

    def energy_to_stripe(self, energy_kev):
        # In future, this should be configurable per-mirror
        if energy_kev < 7:
            return MirrorStripe.BARE
        else:
            return MirrorStripe.RHODIUM
