from ophyd_async.core import StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZStage


class ShutterState(StrictEnum):
    CLOSED = "Closed"
    OPEN = "Open"


class DetectorMotion(XYZStage):
    _device_prefix = "-MO-DET-01:"
    _pmac_prefix = "-MO-PMAC-02:"

    def __init__(self, prefix: str, name: str = ""):
        device_prefix = f"{prefix}{self._device_prefix}"
        pmac_prefix = f"{prefix}{self._pmac_prefix}"

        self.upstream_x = Motor(f"{device_prefix}UPSTREAMX")
        self.downstream_x = Motor(f"{device_prefix}DOWNSTREAMX")
        self.yaw = Motor(f"{device_prefix}YAW")

        self.shutter = epics_signal_rw(
            ShutterState, f"{device_prefix}SET_SHUTTER_STATE"
        )
        self.shutter_closed_lim = epics_signal_r(
            float, f"{device_prefix}CLOSE_LIMIT"
        )  # on limit = 1, off = 0
        self.shutter_open_lim = epics_signal_r(
            float, f"{device_prefix}OPEN_LIMIT"
        )  # on limit = 1, off = 0
        self.z_disabled = epics_signal_r(
            float, f"{device_prefix}Z:DISABLED"
        )  # robot interlock, 0=ok to move, 1=blocked
        self.crate_power = epics_signal_r(
            float, f"{pmac_prefix}CRATE2_HEALTHY"
        )  # returns 0 if no power
        self.in_robot_load_safe_position = epics_signal_r(
            int, f"{pmac_prefix}GPIO_INP_BITS.B2"
        )  # returns 1 if safe

        super().__init__(device_prefix, name)
