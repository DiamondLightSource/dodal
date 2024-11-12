import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
from enum import Enum
from uuid import uuid4

from aiohttp import ClientResponse, ClientSession
from bluesky.protocols import Flyable, Stoppable
from ophyd_async.core import (
    AsyncStatus,
    DeviceVector,
    StandardReadable,
    observe_value,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_r
from redis.asyncio import StrictRedis

from dodal.log import LOGGER


async def get_next_jpeg(response: ClientResponse) -> bytes:
    JPEG_START_BYTE = b"\xff\xd8"
    JPEG_STOP_BYTE = b"\xff\xd9"
    while True:
        line = await response.content.readline()
        if line.startswith(JPEG_START_BYTE):
            return line + await response.content.readuntil(JPEG_STOP_BYTE)


class Source(Enum):
    FULL_SCREEN = 0
    ROI = 1


class OAVSource(StandardReadable):
    def __init__(
        self,
        prefix: str,
        oav_name: str,
    ):
        self.url = epics_signal_r(str, f"{prefix}MJPG_URL_RBV")
        self.oav_name = oav_name
        super().__init__()


class OAVToRedisForwarder(StandardReadable, Flyable, Stoppable):
    """Forwards OAV image data to redis. To use call:

    > bps.kickoff(oav_forwarder)
    > bps.monitor(oav_forwarder.uuid)
    > bps.complete(oav_forwarder)

    """

    DATA_EXPIRY_DAYS = 7

    # This timeout is the maximum time that the forwarder can be streaming for
    TIMEOUT = 30

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
        self.counter = epics_signal_r(int, f"{prefix}CAM:ArrayCounter_RBV")

        self.sources = DeviceVector(
            {
                Source.ROI.value: OAVSource(f"{prefix}MJPG:", "roi"),
                Source.FULL_SCREEN.value: OAVSource(f"{prefix}XTAL:", "fullscreen"),
            }
        )
        self.selected_source = soft_signal_rw(int)

        self.forwarding_task = None
        self.redis_client = StrictRedis(
            host=redis_host, password=redis_password, db=redis_db
        )

        self._stop_flag = asyncio.Event()

        self.sample_id = soft_signal_rw(int, initial_value=0)

        with self.add_children_as_readables():
            # The uuid that images are being saved under, this should be monitored for
            # callbacks to correlate the data
            self.uuid, self.uuid_setter = soft_signal_r_and_setter(str)

        super().__init__(name=name)

    async def _get_frame_and_put_to_redis(
        self, redis_uuid: str, response: ClientResponse
    ):
        """Stores the raw bytes of the jpeg image in redis. Murko ultimately wants a
        pickled numpy array of pixel values but raw byes are more space efficient. There
        may be better ways of doing this, see https://github.com/DiamondLightSource/mx-bluesky/issues/592"""
        jpeg_bytes = await get_next_jpeg(response)
        self.uuid_setter(redis_uuid)
        sample_id = await self.sample_id.get_value()
        redis_key = f"murko:{sample_id}:raw"
        await self.redis_client.hset(redis_key, redis_uuid, jpeg_bytes)  # type: ignore
        await self.redis_client.expire(redis_key, timedelta(days=self.DATA_EXPIRY_DAYS))

    async def _open_connection_and_do_function(
        self, function_to_do: Callable[[ClientResponse, OAVSource], Awaitable]
    ):
        source_idx = await self.selected_source.get_value()
        LOGGER.info(
            f"Forwarding data from sample {await self.sample_id.get_value()} and OAV {source_idx}"
        )
        source = self.sources[source_idx]
        stream_url = await source.url.get_value()
        async with ClientSession() as session:
            async with session.get(stream_url) as response:
                await function_to_do(response, source)

    async def _stream_to_redis(self, response: ClientResponse, source: OAVSource):
        """Uses the update of the frame counter as a trigger to pull an image off the OAV
        and into redis.

        The frame counter is continually increasing on the timescales we store data and
        so can be used as a uuid. If the OAV is updating too quickly we may drop frames
        but in this case a best effort on getting as many frames as possible is sufficient.
        """
        done_status = AsyncStatus(
            asyncio.wait_for(self._stop_flag.wait(), timeout=self.TIMEOUT)
        )
        async for frame_count in observe_value(self.counter, done_status=done_status):
            redis_uuid = f"{source.oav_name}-{frame_count}-{uuid4()}"
            await self._get_frame_and_put_to_redis(redis_uuid, response)

    async def _confirm_mjpg_stream(self, response: ClientResponse, source: OAVSource):
        if response.content_type != "multipart/x-mixed-replace":
            raise ValueError(f"{await source.url.get_value()} is not an MJPG stream")

    @AsyncStatus.wrap
    async def kickoff(self):
        self._stop_flag.clear()
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
            LOGGER.info(
                f"Stopping forwarding for source id {await self.selected_source.get_value()}"
            )
            self._stop_flag.set()
            await self.forwarding_task
