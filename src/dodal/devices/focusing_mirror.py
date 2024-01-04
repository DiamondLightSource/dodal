from enum import Enum
from typing import Any

from ophyd import Component, Device, EpicsMotor, EpicsSignal
from ophyd.status import Status, StatusBase

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
    """Abstract the bimorph mirror voltage PVs into a single device that can be set asynchronously and returns when
    the demanded voltage setpoint is accepted, without blocking the caller as this process can take significant time.
    """

    _actual_v: EpicsSignal = Component(EpicsSignal, "R")
    _setpoint_v: EpicsSignal = Component(EpicsSignal, "D")
    _demand_accepted: EpicsSignal = Component(EpicsSignal, "DSEV")

    def set(self, value, *args, **kwargs) -> StatusBase:
        """Combine the following operations into a single set:
        1. apply the value to the setpoint PV
        2. Return to the caller with a Status future
        3. Wait until demand is accepted
        4. When either demand is accepted or DEFAULT_SETTLE_TIME expires, signal the result on the Status
        """

        setpoint_v = self._setpoint_v
        demand_accepted = self._demand_accepted

        if setpoint_v.get() == value:
            LOGGER.debug(f"{setpoint_v.name} already at {value} - skipping set")
            return Status(success=True, done=True)

        if demand_accepted.get() != DEMAND_ACCEPTED_OK:
            raise AssertionError(
                f"Attempted to set {setpoint_v.name} when demand is not accepted."
            )

        LOGGER.debug(f"setting {setpoint_v.name} to {value}")
        demand_accepted_status = Status(self, DEFAULT_SETTLE_TIME_S)

        subscription: dict[str, Any] = {"handle": None}

        def demand_check_callback(old_value, value, **kwargs):
            LOGGER.debug(f"Got event old={old_value} new={value}")
            if old_value != DEMAND_ACCEPTED_OK and value == DEMAND_ACCEPTED_OK:
                LOGGER.debug(f"Demand accepted for {setpoint_v.name}")
                subs_handle = subscription.pop("handle", None)
                if subs_handle is None:
                    raise AssertionError("Demand accepted before set attempted")
                demand_accepted.unsubscribe(subs_handle)

                demand_accepted_status.set_finished()
            # else timeout handled by parent demand_accepted_status

        subscription["handle"] = demand_accepted.subscribe(demand_check_callback)
        setpoint_status = setpoint_v.set(value)
        status = setpoint_status & demand_accepted_status
        return status


class VFMMirrorVoltages(Device):
    def __init__(self, *args, daq_configuration_path: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.voltage_lookup_table_path = (
            daq_configuration_path + "/json/mirrorFocus.json"
        )

    _channel14_voltage_device = Component(MirrorVoltageDevice, "BM:V14")
    _channel15_voltage_device = Component(MirrorVoltageDevice, "BM:V15")
    _channel16_voltage_device = Component(MirrorVoltageDevice, "BM:V16")
    _channel17_voltage_device = Component(MirrorVoltageDevice, "BM:V17")
    _channel18_voltage_device = Component(MirrorVoltageDevice, "BM:V18")
    _channel19_voltage_device = Component(MirrorVoltageDevice, "BM:V19")
    _channel20_voltage_device = Component(MirrorVoltageDevice, "BM:V20")
    _channel21_voltage_device = Component(MirrorVoltageDevice, "BM:V21")

    @property
    def voltage_channels(self) -> list[MirrorVoltageDevice]:
        return [
            self._channel14_voltage_device,
            self._channel15_voltage_device,
            self._channel16_voltage_device,
            self._channel17_voltage_device,
            self._channel18_voltage_device,
            self._channel19_voltage_device,
            self._channel20_voltage_device,
            self._channel21_voltage_device,
        ]


class FocusingMirror(Device):
    """Focusing Mirror"""

    def __init__(self, bragg_to_lat_lut_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bragg_to_lat_lookup_table_path = bragg_to_lat_lut_path

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

    def energy_to_stripe(self, energy_kev):
        # In future, this should be configurable per-mirror
        if energy_kev < 7:
            return MirrorStripe.BARE
        else:
            return MirrorStripe.RHODIUM
