from ophyd_async.core import Device, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw
from ophyd_async.epics.motor import Motor


class ShutterState(StrictEnum):
    CLOSED = "Closed"
    OPEN = "Open"


class DetectorMotion(Device):
    def __init__(self, prefix: str, name: str = ""):
        device_prefix = "-MO-DET-01:"
        pmac_prefix = "-MO-PMAC-02:"

        self.upstream_x = Motor(f"{prefix}{device_prefix}UPSTREAMX")
        self.downstream_x = Motor(f"{prefix}{device_prefix}DOWNSTREAMX")
        self.x = Motor(f"{prefix}{device_prefix}X")
        self.y = Motor(f"{prefix}{device_prefix}Y")
        self.z = Motor(f"{prefix}{device_prefix}Z")
        self.yaw = Motor(f"{prefix}{device_prefix}YAW")

        self.shutter = epics_signal_rw(
            ShutterState, f"{prefix}{device_prefix}SET_SHUTTER_STATE"
        )
        self.shutter_closed_lim = epics_signal_r(
            float, f"{prefix}{device_prefix}CLOSE_LIMIT"
        )  # on limit = 1, off = 0
        self.shutter_open_lim = epics_signal_r(
            float, f"{prefix}{device_prefix}OPEN_LIMIT"
        )  # on limit = 1, off = 0
        self.z_disabled = epics_signal_r(
            float, f"{prefix}{device_prefix}Z:DISABLED"
        )  # robot interlock, 0=ok to move, 1=blocked
        self.crate_power = epics_signal_r(
            float, f"{prefix}{pmac_prefix}CRATE2_HEALTHY"
        )  # returns 0 if no power
        self.in_robot_load_safe_position = epics_signal_r(
            int, f"{prefix}{pmac_prefix}GPIO_INP_BITS.B2"
        )  # returns 1 if safe

        super().__init__(name)
