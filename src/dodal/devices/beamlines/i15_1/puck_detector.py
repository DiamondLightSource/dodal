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
    """A device that checks the state of pucks on the i15-1 table.

    The pucks on the table that the robot loads from are shipped with lids. Robot loading
    these (or locations where there is no puck) can cause issues. To protect from this
    there is a service running that uses some image detection to determine if a puck is
    at a location and if it has a lid or not. This device exposes this information.

    To get the data first trigger this device then read from the puck you are interested
    in e.g.

    >>> bps.trigger(puck_detect)
    >>> assert bps.rd(puck_detect.puck_states[1]) == PuckState.PUCK

    Note that the pucks are 1-indexed to match the data from the detection algorithm
    """

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
