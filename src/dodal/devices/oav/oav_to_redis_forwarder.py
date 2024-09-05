import asyncio
import io
import pickle
import uuid
from collections.abc import Awaitable, Callable
from datetime import timedelta

import numpy as np
from aiohttp import ClientResponse, ClientSession
from bluesky.protocols import Flyable, Stoppable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.core.signal import soft_signal_r_and_setter, soft_signal_rw
from ophyd_async.epics.signal import epics_signal_r
from PIL import Image
from redis.asyncio import StrictRedis

from dodal.log import LOGGER


async def get_next_jpeg(response: ClientResponse) -> bytes:
    JPEG_START_BYTE = b"\xff\xd8"
    JPEG_STOP_BYTE = b"\xff\xd9"
    while True:
        line = await response.content.readline()
        if line.startswith(JPEG_START_BYTE):
            return line + await response.content.readuntil(JPEG_STOP_BYTE)


class OAVToRedisForwarder(StandardReadable, Flyable, Stoppable):
    """Forwards OAV image data to redis. To use call:

    > bps.kickoff(oav_forwarder)
    > bps.monitor(oav_forwarder.uuid)
    > bps.complete(oav_forwarder)

    """

    DATA_EXPIRY_DAYS = 7

    def __init__(
        self,
        prefix: str,
        redis_host: str,
        redis_password: str,
        redis_db: int = 0,
        name: str = "",
    ) -> None:
        """Reads image data from the MJPEG stream on an OAV and forwards it into a
        redis database. This is currently only used for murko integration.

        Arguments:
            prefix: str             the PV prefix of the OAV
            redis_host: str         the host where the redis database is running
            redis_password: str     the password for the redis database
            redis_db: int           which redis database to connect to, defaults to 0
            name: str               the name of this device
        """
        self.stream_url = epics_signal_r(str, f"{prefix}MJPG:MJPG_URL_RBV")

        with self.add_children_as_readables():
            self.uuid, self.uuid_setter = soft_signal_r_and_setter(str)

        self.forwarding_task = None
        self.redis_client = StrictRedis(
            host=redis_host, password=redis_password, db=redis_db
        )

        self._stop_flag = False

        self.sample_id = soft_signal_rw(int, initial_value=0)

        # The uuid that images are being saved under, this should be monitored for
        # callbacks to correlate the data
        self.uuid, self.uuid_setter = soft_signal_r_and_setter(str)

        super().__init__(name=name)

    async def _get_frame_and_put_to_redis(self, response: ClientResponse):
        """Converts the data that comes in as a jpeg byte stream into a numpy array of
        RGB values, pickles this array then writes it to redis.
        """
        jpeg_bytes = await get_next_jpeg(response)
        self.uuid_setter(image_uuid := str(uuid.uuid4()))
        img = Image.open(io.BytesIO(jpeg_bytes))
        image_data = pickle.dumps(np.asarray(img))
        sample_id = str(await self.sample_id.get_value())
        await self.redis_client.hset(sample_id, image_uuid, image_data)  # type: ignore
        await self.redis_client.expire(sample_id, timedelta(days=self.DATA_EXPIRY_DAYS))
        LOGGER.debug(f"Sent frame to redis key {sample_id} with uuid {image_uuid}")

    async def _open_connection_and_do_function(
        self, function_to_do: Callable[[ClientResponse, str | None], Awaitable]
    ):
        stream_url = await self.stream_url.get_value()
        async with ClientSession() as session:
            async with session.get(stream_url) as response:
                await function_to_do(response, stream_url)

    async def _stream_to_redis(self, response, _):
        while not self._stop_flag:
            await self._get_frame_and_put_to_redis(response)
            await asyncio.sleep(0.01)

    async def _confirm_mjpg_stream(self, response, stream_url):
        if response.content_type != "multipart/x-mixed-replace":
            raise ValueError(f"{stream_url} is not an MJPG stream")

    @AsyncStatus.wrap
    async def kickoff(self):
        self._stop_flag = False
        await self._open_connection_and_do_function(self._confirm_mjpg_stream)
        self.forwarding_task = asyncio.create_task(
            self._open_connection_and_do_function(self._stream_to_redis)
        )

    @AsyncStatus.wrap
    async def complete(self):
        assert self.forwarding_task, "Device not kicked off"
        await self.stop()

    @AsyncStatus.wrap
    async def stop(self, success=True):
        if self.forwarding_task:
            self._stop_flag = True
            await self.forwarding_task
