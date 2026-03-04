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
    def __init__(
        self, puck_detect_url: str, number_of_pucks: int = 20, name: str = ""
    ) -> None:
        self.url = puck_detect_url
        self.number_of_pucks = number_of_pucks

        states, self._setters = zip(
            *[
                soft_signal_r_and_setter(PuckState, initial_value=PuckState.NO_PUCK)
                for _ in range(number_of_pucks)
            ],
            strict=True,
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
                results = data["result"]
                if len(results) != self.number_of_pucks:
                    raise ValueError(
                        f"Puck detect camera returned {len(results)} results but expected {self.number_of_pucks}"
                    )
                for puck_idx, puck_state in data["result"].items():
                    self._setters[int(puck_idx) - 1](PuckState(puck_state))
