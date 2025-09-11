from ophyd_async.core import StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZStage


class ShutterState(StrictEnum):
    """
    Enumeration representing the possible states of a detector shutter.

    Attributes:
        CLOSED: Indicates that the shutter is closed.
        OPEN: Indicates that the shutter is open.
    """

    CLOSED = "Closed"
    OPEN = "Open"


class DetectorMotion(XYZStage):
    """
    A device class representing the motion control and status signals for a detector system.

    Inherits from:
        XYZStage

    Args:
        device_prefix (str): The base prefix for all EPICS process variables.
        pmac_prefix (str): The base prefix for PMAC
        name (str, optional): An optional name for the device.

    Attributes:
        upstream_x (Motor): Motor controlling the upstream X position.
        downstream_x (Motor): Motor controlling the downstream X position.
        yaw (Motor): Motor controlling the yaw rotation.
        shutter (EpicsSignalRW[ShutterState]): Read/write signal for the detector shutter state.
        shutter_closed_lim (EpicsSignalR[float]): Read-only signal indicating if the shutter is at the closed limit (1 = closed, 0 = not closed).
        shutter_open_lim (EpicsSignalR[float]): Read-only signal indicating if the shutter is at the open limit (1 = open, 0 = not open).
        z_disabled (EpicsSignalR[float]): Read-only signal indicating if Z motion is disabled by the robot interlock (0 = ok to move, 1 = blocked).
        crate_power (EpicsSignalR[float]): Read-only signal indicating if the crate power is healthy (0 = no power).
        in_robot_load_safe_position (EpicsSignalR[int]): Read-only signal indicating if the detector is in a robot load safe position (1 = safe).

    """

    def __init__(self, device_prefix: str, pmac_prefix: str, name: str = ""):
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
