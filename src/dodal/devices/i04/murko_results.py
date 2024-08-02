import asyncio
import json

import redis.asyncio as redis
from bluesky.protocols import Flyable
from ophyd_async.core import StandardReadable
from ophyd_async.core.async_status import AsyncStatus
from ophyd_async.core.signal import soft_signal_r_and_setter
from pydantic.dataclasses import dataclass

from dodal.log import LOGGER


@dataclass
class MurkoResult:
    center: tuple[int, int]
    microns_per_pixel: tuple[float, float]
    omega: float


class MurkoResults(StandardReadable, Flyable):
    def __init__(self, name="", prefix="", host="localhost", port=6379, db=0):
        self.redis_client = redis.StrictRedis(host=host, port=port, db=db)
        self.listening_task = None
        with self.add_children_as_readables():
            self.results, self._results_setter = soft_signal_r_and_setter(
                list[MurkoResult], []
            )
        super().__init__(name)

    async def _listen_and_do(self, pubsub):
        while True:
            message = await pubsub.get_message()
            await asyncio.sleep(0.1)
            if message and message["type"] == "message":
                murko_data = json.loads(message["data"])[0]
                LOGGER.info(f"Got {murko_data} from murko")
                metadata = json.loads(
                    await self.redis_client.hget("test-metadata", murko_data["uuid"])
                )
                results = await self.results.get_value()
                results.append(
                    MurkoResult(
                        (murko_data["x_pixel_coord"], murko_data["y_pixel_coord"]),
                        (
                            metadata["microns_per_x_pixel"],
                            metadata["microns_per_x_pixel"],
                        ),
                        metadata["omega_angle"],
                    )
                )
                self._results_setter(results)

    @AsyncStatus.wrap
    async def kickoff(self):
        channel = "murko-results"
        async with self.redis_client.pubsub() as pubsub:
            await pubsub.subscribe(channel)
            print(f"Subscribed to channel: {channel}")
            self.listening_task = asyncio.create_task(self._listen_and_do(pubsub))

    @AsyncStatus.wrap
    async def complete(self):
        assert self.listening_task
        self.listening_task.cancel()
