import asyncio
import io
import pickle
import time
import uuid

import numpy as np
from aiohttp import ClientResponse, ClientSession
from bluesky.protocols import Flyable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.core.signal import soft_signal_r_and_setter
from ophyd_async.epics.signal import epics_signal_r
from PIL import Image
from redis.asyncio import StrictRedis

from dodal.log import LOGGER


class OAVToRedisForwarder(StandardReadable, Flyable):
    def __init__(
        self,
        prefix: str,
        redis_host: str,
        redis_password: str,
        redis_db: int = 0,
        name: str = "",
    ) -> None:
        self.stream_url = epics_signal_r(str, f"{prefix}-DI-OAV-01:MJPG:HOST_RBV")

        with self.add_children_as_readables():
            self.uuid, self.uuid_setter = soft_signal_r_and_setter(str)

        self.forwarding_task = None
        self.redis_client = StrictRedis(
            host=redis_host, password=redis_password, db=redis_db
        )
        self.uuid, self.uuid_setter = soft_signal_r_and_setter(str)

        super().__init__(name=name)

    async def _get_next_jpeg(self, response: ClientResponse) -> bytes:
        JPEG_START_BYTE = b"\xff\xd8"
        JPEG_STOP_BYTE = b"\xff\xd9"
        while True:
            line = await response.content.readline()
            if line.startswith(JPEG_START_BYTE):
                return line + await response.content.readuntil(JPEG_STOP_BYTE)

    async def forward_to_redis(self):
        last_time = time.time()
        stream_url = await self.stream_url.get_value()
        async with ClientSession() as session:
            async with session.get(stream_url) as response:
                while True:
                    jpeg_bytes = await self._get_next_jpeg(response)
                    image_uuid = str(uuid.uuid4())
                    self.uuid_setter(image_uuid)
                    img = Image.open(io.BytesIO(jpeg_bytes))
                    image_data = pickle.dumps(np.asarray(img))
                    await self.redis_client.hset("test-image", image_uuid, image_data)  # type: ignore
                    LOGGER.info(
                        f"Sent frame to redis. Frame speed {1/(time.time()-last_time)} Hz"
                    )
                    last_time = time.time()
                    await asyncio.sleep(0.01)

    @AsyncStatus.wrap
    async def kickoff(self):
        self.forwarding_task = asyncio.create_task(self.forward_to_redis())

    @AsyncStatus.wrap
    async def complete(self):
        assert self.forwarding_task, "Device not kicked off"
        self.forwarding_task.cancel()
