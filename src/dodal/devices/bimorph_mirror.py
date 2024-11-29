import asyncio

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, DeviceVector, StandardReadable, wait_for_value
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw_rbv, epics_signal_x


class BimorphMirrorChannel(StandardReadable):
    def __init__(self, prefix: str, name=""):
        with self.add_children_as_readables(Format.HINTED_SIGNAL):
            self.vtrgt = epics_signal_rw_rbv(float, f"{prefix}:VTRGT")
            self.vout = epics_signal_rw_rbv(float, f"{prefix}:VOUT")
            self.status = epics_signal_r(str, f"{prefix}:STATUS")

        super().__init__(name=name)

class BimorphMirror(StandardReadable, Movable):
    def __init__(self, prefix: str, name="", number_of_channels: int = 0):
        self.number_of_channels = number_of_channels

        with self.add_children_as_readables():
            self.channels = DeviceVector(
                {
                    i: BimorphMirrorChannel(f"{prefix}:C{i}", f"channel{i}")
                    for i in range(1, number_of_channels + 1)
                }
            )
        self.alltrgt_proc = epics_signal_x(f"{prefix}:ALLTRGT.PROC")
        self.status = epics_signal_r(str, f"{prefix}:STATUS")

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: dict[int, float]):
        for i in value.keys():
            assert self.channels.get(i) is not None

        await asyncio.gather(
            *[self.channels.get(i).vtrgt.set(target) for i, target in value.items()]
        )

        await asyncio.gather(
            *[
                wait_for_value(self.channels.get(i).vtrgt, target, None)
                for i, target in value.items()
            ]
        )

        await self.alltrgt_proc.trigger()

        await asyncio.gather(
            *[
                wait_for_value(self.channels.get(i).vout, target, None)
                for i, target in value.items()
            ]
        )
