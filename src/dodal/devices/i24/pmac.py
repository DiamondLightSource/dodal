import asyncio
from typing import Tuple

from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.core.signal import SignalRW, SignalX
from ophyd_async.core.signal_backend import SignalBackend
from ophyd_async.core.utils import DEFAULT_TIMEOUT
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_rw


class PMACStringHome(SignalX):
    def __init__(
        self,
        pmac_str_sig: SignalRW,
        string_to_send: str,
        backend: SignalBackend,
        timeout: float | None = DEFAULT_TIMEOUT,
        name: str = "",
    ) -> None:
        self.signal = pmac_str_sig
        self.cmd_string = string_to_send
        super().__init__(backend, timeout, name)

    async def trigger(self):
        await self.signal.set(self.cmd_string)


class StageMotors(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")
        super().__init__(name)

    async def _move_stages(self, position: Tuple[float]):
        if len(position) == 2:
            await asyncio.gather(self.x._move(position[0]), self.y._move(position[1]))
        if len(position) == 3:
            await asyncio.gather(
                self.x._move(position[0]),
                self.y._move(position[1]),
                self.z._move(position[2]),
            )

    def set(self, position) -> AsyncStatus:
        return AsyncStatus(self._move_stages(position))


class PMAC(StandardReadable):  # Should it also be a movable?
    """Device to control the chip stage on I24."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.pmac_string = epics_signal_rw(str, prefix + "PMAC_STRING")
        # self.home = PMACStringHome(
        #     self.pmac_string, r"\#1hmz\#2hmz\#3hmz", backend=SoftSignalBackend(str)
        # )

        self.stages = StageMotors(prefix)

        super().__init__(name)
