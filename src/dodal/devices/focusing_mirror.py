from enum import Enum, IntEnum
from typing import Any

from ophyd import Component, Device, EpicsSignal
from ophyd.status import Status, StatusBase
from ophyd_async.core import StandardReadable
from ophyd_async.core.signal import soft_signal_r_and_setter
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import (
    epics_signal_rw,
    epics_signal_x,
)

from dodal.log import LOGGER

VOLTAGE_POLLING_DELAY_S = 0.5

# The default timeout is 60 seconds as voltage slew rate is typically ~2V/s
DEFAULT_SETTLE_TIME_S = 60


class MirrorType(str, Enum):
    """See https://manual.nexusformat.org/classes/base_classes/NXmirror.html"""

    SINGLE = "single"
    MULTI = "multi"


class MirrorStripe(str, Enum):
    RHODIUM = "Rhodium"
    BARE = "Bare"
    PLATINUM = "Platinum"


class MirrorVoltageDemand(IntEnum):
    N_A = 0
    OK = 1
    FAIL = 2
    SLEW = 3


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

        if demand_accepted.get() != MirrorVoltageDemand.OK:
            raise AssertionError(
                f"Attempted to set {setpoint_v.name} when demand is not accepted."
            )

        if setpoint_v.get() == value:
            LOGGER.debug(f"{setpoint_v.name} already at {value} - skipping set")
            return Status(success=True, done=True)

        LOGGER.debug(f"setting {setpoint_v.name} to {value}")
        demand_accepted_status = Status(self, DEFAULT_SETTLE_TIME_S)

        subscription: dict[str, Any] = {"handle": None}

        def demand_check_callback(old_value, value, **kwargs):
            LOGGER.debug(f"Got event old={old_value} new={value} for {setpoint_v.name}")
            if old_value != MirrorVoltageDemand.OK and value == MirrorVoltageDemand.OK:
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


class FocusingMirror(StandardReadable):
    """Focusing Mirror"""

    def __init__(
        self, name, prefix, bragg_to_lat_lut_path=None, x_suffix="X", y_suffix="Y"
    ):
        self.bragg_to_lat_lookup_table_path = bragg_to_lat_lut_path
        self.yaw_mrad = Motor(prefix + "YAW")
        self.pitch_mrad = Motor(prefix + "PITCH")
        self.roll_mrad = Motor(prefix + "ROLL")
        self.x_mm = Motor(prefix + x_suffix)
        self.y_mm = Motor(prefix + y_suffix)
        self.jack1_mm = Motor(prefix + "Y1")
        self.jack2_mm = Motor(prefix + "Y2")
        self.jack3_mm = Motor(prefix + "Y3")
        self.translation1_mm = Motor(prefix + "X1")
        self.translation2_mm = Motor(prefix + "X2")

        self.type, _ = soft_signal_r_and_setter(MirrorType, MirrorType.SINGLE)
        # The device is in the beamline co-ordinate system so pitch is the incident angle
        # regardless of orientation of the mirror
        self.incident_angle = Motor(prefix + "PITCH")

        self.set_readable_signals(
            read=[self.incident_angle.user_readback],
            config=[self.type],
        )
        super().__init__(name)


class FocusingMirrorWithStripes(FocusingMirror):
    """A focusing mirror where the stripe material can be changed. This is usually done
    based on the energy of the beamline."""

    def __init__(self, name, prefix, *args, **kwargs):
        self.stripe = epics_signal_rw(MirrorStripe, prefix + "STRP:DVAL")
        # apply the current set stripe setting
        self.apply_stripe = epics_signal_x(prefix + "CHANGE.PROC")

        super().__init__(name, prefix, *args, **kwargs)

    def energy_to_stripe(self, energy_kev) -> MirrorStripe:
        # In future, this should be configurable per-mirror
        if energy_kev < 7:
            return MirrorStripe.BARE
        else:
            return MirrorStripe.RHODIUM
