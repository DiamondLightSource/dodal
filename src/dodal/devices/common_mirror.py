from typing import Generic, TypeVar

from bluesky.protocols import Locatable, Location, Stoppable
from ophyd_async.core import AsyncStatus, StrictEnum
from ophyd_async.epics.core import epics_signal_rw, epics_signal_x

from dodal.devices.motors import XYZPitchYawRollStage

DEFAULT_MIRROR_READ_SUFFIX = "MIRCTRL:RBV:MIRROR"
DEFAULT_MIRROR_WRITE_SUFFIX = "MIRCTRL:DMD:MIRROR"
DEFAULT_MIRROR_CHANGE_SUFFIX = "MIRCTRL:SEQ:CHNG:MIRROR.PROC"
DEFAULT_MIRROR_ABORT_SUFFIX = "MIRCTRL:DMD:ABORT.PROC"
DEFAULT_FPITCH_READ_SUFFIX = "FPITCH:RBV"
DEFAULT_FPITCH_WRITE_SUFFIX = "FPITCH:DMD"


TMirror = TypeVar("TMirror", bound=StrictEnum)


class XYZSwitchingMirror(
    XYZPitchYawRollStage, Generic[TMirror], Locatable[TMirror], Stoppable
):
    """Set of mirrors on hexapod stage.

    This device controls set of mirrors on a hexapod stage with standard x,y,z and yaw,
    pitch, roll motors.

    Args:
        prefix (str): EPICS PV prefix for the mirror.
        mirrors (StrictEnum): enum representing set of mirrors
        fpitch_read_suffix (str, optional): suffix for the fine pitch readback PV
        fpitch_write_suffix (str, optional): suffix for the fine pitch setpoint PV
        mirror_read_suffix (str, optional): suffix for mirror readback PV
        mirror_write_suffix (str, optional): suffix for mirror demand PV
        mirror_abort_suffix (str, optional): suffix for mirror abort PV
        name (str, optional): name of the device.
    """

    def __init__(
        self,
        prefix: str,
        mirrors: type[TMirror],
        mirror_read_suffix: str = DEFAULT_MIRROR_READ_SUFFIX,
        mirror_write_suffix: str = DEFAULT_MIRROR_WRITE_SUFFIX,
        mirror_change_suffix: str = DEFAULT_MIRROR_CHANGE_SUFFIX,
        mirror_abort_suffix: str = DEFAULT_MIRROR_ABORT_SUFFIX,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.mirror = epics_signal_rw(
                mirrors,
                read_pv=prefix + mirror_read_suffix,
                write_pv=prefix + mirror_write_suffix,
            )

        self.mirror_change = epics_signal_x(write_pv=prefix + mirror_change_suffix)
        self.mirror_abort = epics_signal_x(write_pv=prefix + mirror_abort_suffix)

        super().__init__(prefix=prefix, name=name)

    @AsyncStatus.wrap
    async def set(self, new_position: TMirror):
        await self.mirror.set(new_position)
        await self.mirror_change.trigger()

    async def locate(self) -> Location[TMirror]:
        location = await self.mirror.locate()
        return location

    async def stop(self, success=True) -> None:
        await self.mirror_abort.trigger()


class XYZPiezoCollimatingMirror(XYZPitchYawRollStage):
    """Collimating mirror on a hexapod stage.

    This device controls mirror on a hexapod stage which includes standard x, y, z, yaw,
    pitch and roll motors, as well as fine pitch piezo motor.

    Args:
        prefix (str): EPICS PV prefix for the mirror.
        fpitch_read_suffix (str, optional): The suffix for the fine pitch readback PV.
        fpitch_write_suffix (str, optional): The suffix for the fine pitch setpoint PV.
        name (str, optional): The name of the device.
    """

    def __init__(
        self,
        prefix: str,
        fpitch_read_suffix: str = "FPITCH:RBV:AI",
        fpitch_write_suffix: str = "FPITCH:DMD:AO",
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.fine_pitch = epics_signal_rw(
                float,
                read_pv=prefix + fpitch_read_suffix,
                write_pv=prefix + fpitch_write_suffix,
            )
        super().__init__(prefix=prefix, name=name)


class XYZPiezoSwitchingMirror(XYZSwitchingMirror[TMirror], Generic[TMirror]):
    """Set of mirrors on a hexapod stage with piezo fine pitch motor.

    This device controls set of mirrors on a hexapod stage which includes standard x,
    y, z, yaw, pitch and roll motors, as well as fine pitch piezo motor.

    Args:
        prefix (str): EPICS PV prefix for the mirror.
        mirrors (StrictEnum): enum representing set of mirrors
        fpitch_read_suffix (str, optional): suffix for the fine pitch readback PV
        fpitch_write_suffix (str, optional): suffix for the fine pitch setpoint PV
        mirror_read_suffix (str, optional): suffix for mirror readback PV
        mirror_write_suffix (str, optional): suffix for mirror demand PV
        mirror_abort_suffix (str, optional): suffix for mirror abort PV
        name (str, optional): name of the device.
    """

    def __init__(
        self,
        prefix: str,
        mirrors: type[TMirror],
        fpitch_read_suffix: str = DEFAULT_FPITCH_READ_SUFFIX,
        fpitch_write_suffix: str = DEFAULT_FPITCH_WRITE_SUFFIX,
        mirror_read_suffix: str = DEFAULT_MIRROR_READ_SUFFIX,
        mirror_write_suffix: str = DEFAULT_MIRROR_WRITE_SUFFIX,
        mirror_change_suffix: str = DEFAULT_MIRROR_CHANGE_SUFFIX,
        mirror_abort_suffix: str = DEFAULT_MIRROR_ABORT_SUFFIX,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.fine_pitch = epics_signal_rw(
                float,
                read_pv=prefix + fpitch_read_suffix,
                write_pv=prefix + fpitch_write_suffix,
            )
        super().__init__(
            prefix=prefix,
            mirrors=mirrors,
            mirror_read_suffix=mirror_read_suffix,
            mirror_write_suffix=mirror_write_suffix,
            mirror_change_suffix=mirror_change_suffix,
            mirror_abort_suffix=mirror_abort_suffix,
            name=name,
        )
