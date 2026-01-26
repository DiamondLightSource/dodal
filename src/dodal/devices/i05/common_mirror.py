from typing import Generic, TypeVar

from bluesky.protocols import Locatable, Location, Stoppable
from ophyd_async.core import AsyncStatus, StrictEnum
from ophyd_async.epics.core import epics_signal_rw, epics_signal_x

from dodal.devices.motors import XYZPitchYawRollStage

TMirror = TypeVar("TMirror", bound=StrictEnum)


class XYZSwitchingMirror(
    XYZPitchYawRollStage, Generic[TMirror], Locatable[TMirror], Stoppable
):
    """
    A device represention set of mirrors on a hexapod stage with x,y,z and yaw, pitch, roll motors.
    To change mirror set mirror enum and trigger mirror change.
    """

    def __init__(
        self,
        prefix: str,
        mirrors: type[TMirror],
        name: str = "",
        mirror_read_suffix: str = "MIRCTRL:RBV:MIRROR",
        mirror_write_suffix: str = "MIRCTRL:DMD:MIRROR",
        mirror_change_suffix: str = "MIRCTRL:SEQ:CHNG:MIRROR.PROC",
        mirror_abort_suffix: str = "MIRCTRL:DMD:ABORT.PROC",
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
    """
    Collimating mirror on a hexapod stage with x,y,z and yaw, pitch, roll motors, including a fine pitch piezo motor.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        fpitch_read_suffix: str = "FPITCH:RBV",
        fpitch_write_suffix: str = "FPITCH:DMD",
    ):
        with self.add_children_as_readables():
            self.fine_pitch = epics_signal_rw(
                float,
                read_pv=prefix + fpitch_read_suffix,
                write_pv=prefix + fpitch_write_suffix,
            )
        super().__init__(prefix=prefix, name=name)


class XYZPiezoSwitchingMirror(
    XYZPitchYawRollStage, Generic[TMirror], Locatable[TMirror], Stoppable
):
    """
    A device represention set of mirrors on a hexapod stage with x,y,z and yaw, pitch, roll motors, including a fine pitch piezo motor.
    """

    def __init__(
        self,
        prefix: str,
        mirrors: type[TMirror],
        name: str = "",
        fpitch_read_suffix: str = "FPITCH:RBV",
        fpitch_write_suffix: str = "FPITCH:DMD",
        mirror_read_suffix: str = "MIRCTRL:RBV:MIRROR",
        mirror_write_suffix: str = "MIRCTRL:DMD:MIRROR",
        mirror_change_suffix: str = "MIRCTRL:SEQ:CHNG:MIRROR.PROC",
        mirror_abort_suffix: str = "MIRCTRL:DMD:ABORT.PROC",
    ):
        with self.add_children_as_readables():
            self.fine_pitch = epics_signal_rw(
                float,
                read_pv=prefix + fpitch_read_suffix,
                write_pv=prefix + fpitch_write_suffix,
            )
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
