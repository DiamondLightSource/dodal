import json

from aiohttp import ClientSession
from ophyd_async.core import (
    AsyncStatus,
    DeviceVector,
    SignalR,
    StandardReadable,
    StrictEnum,
    soft_signal_r_and_setter,
)


class PuckState(StrictEnum):
    NO_PUCK = "None"
    PUCK = "Puck"
    LID = "Lid"


class PuckDetect(StandardReadable):
    def __init__(self, puck_detect_url: str, name: str = "") -> None:
        self.url = puck_detect_url

        states, self._setters = zip(
            *[soft_signal_r_and_setter(PuckState) for _ in range(20)], strict=True
        )

        # States are 1 indexed to match the convention from the detection code
        self.puck_states: DeviceVector[SignalR[PuckState]] = DeviceVector(
            {i: states[i - 1] for i in range(1, len(states) + 1)}
        )
        super().__init__(name)

    @AsyncStatus.wrap
    async def trigger(self):
        async with ClientSession(raise_for_status=True) as session:
            async with session.get(self.url) as response:
                raw_data = await response.read()
                data = json.loads(raw_data)
                self._setters[0](PuckState(data["result"]["1"]))
