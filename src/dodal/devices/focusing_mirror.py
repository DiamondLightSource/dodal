import time
from enum import Enum

from ophyd import Component, Device, EpicsMotor, EpicsSignal
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


class MirrorVoltageDevice(Device):
    _actual_v: EpicsSignal = Component(EpicsSignal, "R")
    _setpoint_v: EpicsSignal = Component(EpicsSignal, "D")
    _demand_accepted: EpicsSignal = Component(EpicsSignal, "DSEV")

    def set(self, value, *, timeout=None, settle_time=0, **kwargs):
        setpoint_v = self._setpoint_v
        demand_accepted = self._demand_accepted

        LOGGER.debug(f"setting {setpoint_v.name} to {value}")
        setpoint_status = setpoint_v.set(value)
        demand_accepted_status = Status(self, DEFAULT_SETTLE_TIME_S)

        def demand_check_callback(expiry_time_s):
            accepted = demand_accepted.get()
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
                    accepted = demand_accepted.get()
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
    _channel14_voltage_device: MirrorVoltageDevice = Component(
        MirrorVoltageDevice, "BM:V14"
    )
    _channel15_voltage_device: MirrorVoltageDevice = Component(
        MirrorVoltageDevice, "BM:V15"
    )
    _channel16_voltage_device: MirrorVoltageDevice = Component(
        MirrorVoltageDevice, "BM:V16"
    )
    _channel17_voltage_device: MirrorVoltageDevice = Component(
        MirrorVoltageDevice, "BM:V17"
    )
    _channel18_voltage_device: MirrorVoltageDevice = Component(
        MirrorVoltageDevice, "BM:V18"
    )
    _channel19_voltage_device: MirrorVoltageDevice = Component(
        MirrorVoltageDevice, "BM:V19"
    )
    _channel20_voltage_device: MirrorVoltageDevice = Component(
        MirrorVoltageDevice, "BM:V20"
    )
    _channel21_voltage_device: MirrorVoltageDevice = Component(
        MirrorVoltageDevice, "BM:V21"
    )

    voltage_lookup_table_path: str = (
        "/dls_sw/i03/software/daq_configuration/json/mirrorFocus.json"
    )

    @property
    def voltage_channels(self) -> list[MirrorVoltageDevice]:
        return [
            getattr(self, name)
            for name in [
                "_channel14_voltage_device",
                "_channel15_voltage_device",
                "_channel16_voltage_device",
                "_channel17_voltage_device",
                "_channel18_voltage_device",
                "_channel19_voltage_device",
                "_channel20_voltage_device",
                "_channel21_voltage_device",
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
