from enum import IntEnum

# from ophyd import Component as Cpt
# from ophyd import Device, EpicsMotor, EpicsSignal, EpicsSignalRO
from ophyd_async.core import Device
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class ShutterState(IntEnum):
    CLOSED = 0
    OPEN = 1


class DetectorMotion(Device):
    def __init__(self, prefix: str, name: str = ""):
        device_prefix = "-MO-DET-01:"
        self.upstream_x = Motor(f"{prefix}{device_prefix}UPSTREAMX")
        self.downstream_x = Motor(f"{prefix}{device_prefix}DOWNSTREAMX")
        self.x = Motor(f"{prefix}{device_prefix}X")
        self.y = Motor(f"{prefix}{device_prefix}Y")
        self.z = Motor(f"{prefix}{device_prefix}Z")
        self.yaw = Motor(f"{prefix}{device_prefix}YAW")
        self.shutter = Motor(f"{prefix}{device_prefix}SET_SHUTTER_STATE")

        self.shutter = epics_signal_rw(
            float, "-MO-DET-01:SET_SHUTTER_STATE"
        )  # 0=closed, 1=open monitors

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
            float, f"{prefix}{device_prefix}CRATE2_HEALTHY"
        )  # returns 0 if no power
        self.in_robot_load_safe_position = epics_signal_r(
            float, f"{prefix}{device_prefix}GPIO_INP_BITS.B2"
        )  # returns 1 if safe

        super().__init__(name)
