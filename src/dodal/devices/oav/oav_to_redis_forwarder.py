import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
from enum import Enum

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
from ophyd_async.epics.signal import epics_signal_r
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
        self.image_uuid = epics_signal_r(int, f"{prefix}UniqueId_RBV")
        self.oav_name = oav_name


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
        self._sources = DeviceVector(
            {
                Source.ROI.value: OAVSource(f"{prefix}MJPG:", "roi"),
                Source.FULL_SCREEN.value: OAVSource(f"{prefix}XTAL:", "fullscreen"),
            }
        )
        self.selected_source = soft_signal_rw(Source)

        self.forwarding_task = None
        self.redis_client = StrictRedis(
            host=redis_host, password=redis_password, db=redis_db
        )

        self._stop_flag = False

        self.sample_id = soft_signal_rw(int, initial_value=0)

        with self.add_children_as_readables():
            # The uuid that images are being saved under, this should be monitored for
            # callbacks to correlate the data
            self.uuid, self.uuid_setter = soft_signal_r_and_setter(str)

        super().__init__(name=name)

    async def _get_frame_and_put_to_redis(
        self, redis_uuid: str, response: ClientResponse
    ):
        """Converts the data that comes in as a jpeg byte stream into a numpy array of
        RGB values, pickles this array then writes it to redis.
        """
        jpeg_bytes = await get_next_jpeg(response)
        self.uuid_setter(redis_uuid)
        sample_id = await self.sample_id.get_value()
        redis_key = f"murko:{sample_id}:raw"
        await self.redis_client.hset(redis_key, redis_uuid, jpeg_bytes)  # type: ignore
        await self.redis_client.expire(redis_key, timedelta(days=self.DATA_EXPIRY_DAYS))

    async def _open_connection_and_do_function(
        self, function_to_do: Callable[[ClientResponse, OAVSource], Awaitable]
    ):
        source_name = await self.selected_source.get_value()
        LOGGER.info(
            f"Forwarding data from sample {await self.sample_id.get_value()} and OAV {source_name}"
        )
        source = self._sources[source_name.value]
        stream_url = await source.url.get_value()
        async with ClientSession() as session:
            async with session.get(stream_url) as response:
                await function_to_do(response, source)

    async def _stream_to_redis(self, response: ClientResponse, source: OAVSource):
        async for image_uuid in observe_value(source.image_uuid):
            if self._stop_flag:
                break
            redis_uuid = f"{source.name}-{image_uuid}"
            await self._get_frame_and_put_to_redis(redis_uuid, response)

    async def _confirm_mjpg_stream(self, response: ClientResponse, source: OAVSource):
        if response.content_type != "multipart/x-mixed-replace":
            raise ValueError(f"{await source.url.get_value()} is not an MJPG stream")

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
            LOGGER.info(
                f"Stopping forwarding for {await self.selected_source.get_value()}"
            )
            self._stop_flag = True
            await self.forwarding_task
