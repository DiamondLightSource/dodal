from bluesky.protocols import Movable, Status
from ophyd_async.core import (
    AsyncStatus,
    ConfigSignal,
    HintedSignal,
    StandardReadable,
    set_and_wait_for_value,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class Undulator_Gap(StandardReadable, Movable):
    def __init__(self, prefix: str, name: str = ""):
        self.user_setpoint = epics_signal_rw(
            str, prefix + "BLGSET", prefix + "GAPSET.B"
        )
        self.set_move = epics_signal_rw(int, prefix + "BLGSETP")
        with self.add_children_as_readables(ConfigSignal):
            self.motor_egu = epics_signal_r(str, prefix + "BLGAPMTR.EGU")
            self.velocity = epics_signal_rw(float, prefix + "BLGSETVEL")
            self.max_velocity = epics_signal_r(float, prefix + "BLGSETVEL.DRVH")
            self.min_velocity = epics_signal_r(float, prefix + "BLGSETVEL.DRVL")
            self.acceleration_time = epics_signal_r(float, prefix + "IDGSETACC")

        with self.add_children_as_readables(HintedSignal):
            self.user_readback = epics_signal_r(float, prefix + "CURRGAPD")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value) -> Status:
        await self.user_setpoint.set(value=value)
        return await set_and_wait_for_value(signal=self.set_move, value=0)
