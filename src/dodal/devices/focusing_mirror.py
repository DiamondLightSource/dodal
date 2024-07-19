from enum import Enum

from ophyd_async.core import (
    AsyncStatus,
    Device,
    DeviceVector,
    StandardReadable,
    observe_value,
)
from ophyd_async.core.signal import soft_signal_r_and_setter
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import (
    epics_signal_r,
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


class MirrorVoltageDemand(str, Enum):
    N_A = "N/A"
    OK = "OK"
    FAIL = "FAIL"
    SLEW = "SLEW"


class MirrorVoltageDevice(Device):
    """Abstract the bimorph mirror voltage PVs into a single device that can be set asynchronously and returns when
    the demanded voltage setpoint is accepted, without blocking the caller as this process can take significant time.
    """

    def __init__(self, name: str = "", prefix: str = ""):
        self._actual_v = epics_signal_r(int, prefix + "R")
        self._setpoint_v = epics_signal_rw(int, prefix + "D")
        self._demand_accepted = epics_signal_r(MirrorVoltageDemand, prefix + "DSEV")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value, *args, **kwargs):
        """Combine the following operations into a single set:
        1. apply the value to the setpoint PV
        3. Wait until demand is accepted
        4. When either demand is accepted or DEFAULT_SETTLE_TIME expires, signal the result on the Status
        """

        setpoint_v = self._setpoint_v
        demand_accepted = self._demand_accepted

        if await demand_accepted.get_value() != MirrorVoltageDemand.OK:
            raise AssertionError(
                f"Attempted to set {setpoint_v.name} when demand is not accepted."
            )

        if await setpoint_v.get_value() == value:
            LOGGER.debug(f"{setpoint_v.name} already at {value} - skipping set")
            return

        LOGGER.debug(f"setting {setpoint_v.name} to {value}")

        # Register an observer up front to ensure we don't miss events after we
        # perform the set
        demand_accepted_iterator = observe_value(
            demand_accepted, timeout=DEFAULT_SETTLE_TIME_S
        )
        # discard the current value (OK) so we can await a subsequent change
        await anext(demand_accepted_iterator)
        await setpoint_v.set(value)

        # The set should always change to SLEW regardless of whether we are
        # already at the set point, then change back to OK/FAIL depending on
        # success
        accepted_value = await anext(demand_accepted_iterator)
        assert accepted_value == MirrorVoltageDemand.SLEW
        LOGGER.debug(
            f"Demand not accepted for {setpoint_v.name}, waiting for acceptance..."
        )
        while MirrorVoltageDemand.SLEW == (
            accepted_value := await anext(demand_accepted_iterator)
        ):
            pass

        if accepted_value != MirrorVoltageDemand.OK:
            raise AssertionError(
                f"Voltage slew failed for {setpoint_v.name}, new state={accepted_value}"
            )


class VFMMirrorVoltages(StandardReadable):
    def __init__(
        self, name: str, prefix: str, *args, daq_configuration_path: str, **kwargs
    ):
        self.voltage_lookup_table_path = (
            daq_configuration_path + "/json/mirrorFocus.json"
        )
        with self.add_children_as_readables():
            self.voltage_channels = DeviceVector(
                {
                    i - 14: MirrorVoltageDevice(prefix=f"{prefix}BM:V{i}")
                    for i in range(14, 22)
                }
            )
        super().__init__(*args, name=name, **kwargs)


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
