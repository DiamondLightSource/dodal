from enum import Enum
from PIL import Image
import numpy as np
from numpy.typing import NDArray
from ophyd_async.core import StandardReadable, AsyncStatus
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw
from ophyd_async.core.signal import soft_signal_r_and_setter
from dodal.devices.oav.oav_parameters import OAVConfigParams
from bluesky.protocols import Flyable

import redis.asyncio as redis
import time
import aiohttp
import asyncio
import uuid
import pickle
import numpy as np
import io
from dodal.log import LOGGER

class ZoomLevel(str, Enum):
    ONE = "1.0x"
    ONE_AND_A_HALF = "1.5x"
    TWO = "2.0x"
    TWO_AND_A_HALF = "2.5x"
    THREE = "3.0x"
    FIVE = "5.0x"
    SEVEN_AND_A_HALF = "7.5x"
    TEN = "10.0x"


class ZoomController(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.level = epics_signal_rw(ZoomLevel, prefix + "MP:SELECT")
            self.percentage = epics_signal_rw(float, prefix + "ZOOMPOSCMD")
        super().__init__(name=name)

class OAV(StandardReadable, Flyable):
    def __init__(self, prefix: str, params: OAVConfigParams, name: str = "") -> None:
        self.zoom_controller = ZoomController(prefix + "-EA-OAV-01:FZOOM:")
        self.array_data = epics_signal_r(
            NDArray[np.uint8], f"pva://{prefix}-DI-OAV-01:PVA:ARRAY"
        )
        self.x_size = epics_signal_r(int, prefix + "-DI-OAV-01:MJPG:ArraySize1_RBV")
        self.y_size = epics_signal_r(int, prefix + "-DI-OAV-01:MJPG:ArraySize2_RBV")
        self.stream_url = "http://bl04i-di-serv-01.diamond.ac.uk:8080/OAV.mjpg.mjpg"
        self.parameters = params
        self.cb = None
        self.forwarding_task = None
        self.redis_client = redis.StrictRedis(host="i04-control.diamond.ac.uk", password="", db=7)
        self.uuid, self.uuid_setter = soft_signal_r_and_setter(str)

        super().__init__(name=name)
    
    async def forward_to_redis(self):
        last_time = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(self.stream_url) as response:
                while True:
                    line = await response.content.readline()
                    if not line:
                        break
                    # JPEGs start with \xff\xd8 and end with \xff\xd9
                    if line.startswith(b"\xff\xd8"):
                        frame_data = line + await response.content.readuntil(b"\xff\xd9")
                        image_uuid = str(uuid.uuid4())
                        self.uuid_setter(image_uuid)
                        LOGGER.info(f"Converting to image")
                        img = Image.open(io.BytesIO(frame_data))
                        LOGGER.info(f"Converted to image")


                        numpydata = np.asarray(img)
                        LOGGER.info(f"Converted to np array")
                        await self.redis_client.hset("test-image", image_uuid, pickle.dumps(numpydata))
                        LOGGER.info(f"Sent frame to redis. Frame speed {1/(time.time()-last_time)} Hz")
                        last_time = time.time()
                    await asyncio.sleep(0.01)

    @AsyncStatus.wrap
    async def kickoff(self):
        self.forwarding_task = asyncio.create_task(self.forward_to_redis())

    @AsyncStatus.wrap
    async def complete(self):
        self.forwarding_task.cancel()
