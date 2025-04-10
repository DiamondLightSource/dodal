import json
import pickle
from collections import OrderedDict
from enum import Enum
from typing import TypedDict

import numpy as np
from bluesky.protocols import Stageable, Triggerable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from redis.asyncio import StrictRedis

from dodal.devices.flux import Flux
from dodal.devices.i04.constants import RedisConstants
from dodal.devices.oav.oav_calculations import (
    calculate_beam_distance,
    camera_coordinates_to_xyz_mm,
)
from dodal.log import LOGGER

MurkoResult = dict
FullMurkoResults = dict[str, list[MurkoResult]]


class MurkoMetadata(TypedDict):
    zoom_percentage: float
    microns_per_x_pixel: float
    microns_per_y_pixel: float
    beam_centre_i: int
    beam_centre_j: int
    sample_id: str
    omega_angle: float
    uuid: str


class Coord(Enum):
    x = 0
    y = 1
    z = 2


class MurkoResultsDevice(StandardReadable, Triggerable, Stageable):
    """Device that takes crystal centre coords from Murko and uses them to set the
    x, y, z coordinate of the sample to be in line with the beam centre.
    (x, z) coords can be read at 90°, and (x, y) at 180° (or the closest omega angle to
    90° and 180°). The average of the x values at these angles is taken, and sin(omega)z
    and cosine(omega)y are taken to account for the rotation. This value is used to
    calculate a number of mm the sample needs to move to be in line with the beam centre.
    """

    TIMEOUT_S = 2

    def __init__(
        self,
        redis_host=RedisConstants.REDIS_HOST,
        redis_password=RedisConstants.REDIS_PASSWORD,
        redis_db=RedisConstants.MURKO_REDIS_DB,
        name="",
    ):
        self.redis_client = StrictRedis(
            host=redis_host,
            password=redis_password,
            db=redis_db,
        )
        self.pubsub = self.redis_client.pubsub()
        self._last_omega = 0
        self.sample_id = soft_signal_rw(str)  # Should get from redis
        self.stop_angle = 270
        self.sums = {"x": 0, "y": 0, "z": 0}
        self.total = 0

        with self.add_children_as_readables():
            # Diffs from current x/y/z
            self.x_mm, self._x_mm_setter = soft_signal_r_and_setter(float)
            self.y_mm, self._y_mm_setter = soft_signal_r_and_setter(float)
            self.z_mm, self._z_mm_setter = soft_signal_r_and_setter(float)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def stage(self):
        await self.pubsub.subscribe("murko-results")
        self._x_mm_setter(0)
        self._y_mm_setter(0)
        self._z_mm_setter(0)

    @AsyncStatus.wrap
    async def unstage(self):
        await self.pubsub.unsubscribe()

    @AsyncStatus.wrap
    async def trigger(self):
        # Wait for results
        sample_id = await self.sample_id.get_value()
        while self._last_omega < self.stop_angle:
            # waits here for next batch to be recieved
            message = await self.pubsub.get_message(timeout=self.TIMEOUT_S)
            if message is None:  # No more messages to process
                break
            await self.process_batch(message, sample_id)
        avg_x = self.sums["x"] / self.total
        avg_y = self.sums["y"] / self.total
        avg_z = self.sums["z"] / self.total
        self._x_mm_setter(avg_x)
        self._y_mm_setter(avg_y)
        self._z_mm_setter(avg_z)

    async def process_batch(self, message: dict | None, sample_id: str):
        if message and message["type"] == "message":
            batch_results = pickle.loads(message["data"])
            for results in batch_results:
                LOGGER.info(f"Got {results} from redis")
                for uuid, result in results.items():
                    if metadata_str := await self.redis_client.hget(
                        f"murko:{sample_id}:metadata", uuid
                    ):
                        self.process_result(result, uuid, metadata_str)

    def process_result(
        self, result: dict, uuid: int, metadata_str: str
    ) -> float | None:
        metadata = MurkoMetadata(json.loads(metadata_str))
        omega_angle = metadata["omega_angle"]
        LOGGER.info(f"Got angle {omega_angle}")
        # Find closest to next search angle
        movement = self.get_coords(metadata, result, omega_angle)
        LOGGER.info(f"Using result {uuid}, {metadata_str}, {result}")
        for coord in ("x", "y", "z"):
            self.sums[coord] += movement[Coord[coord].value]
            LOGGER.info(f"Found {coord} at {movement}, angle = {omega_angle}")
        print(self.total)
        self.total += 1
        self._last_omega = omega_angle

    def get_coords(
        self, metadata: MurkoMetadata, result: MurkoResult, omega: float
    ) -> np.ndarray:
        """Gets the 'most_likely_click' coordinates from Murko if omega or the last
        omega are the closest angle to the search angle. Otherwise returns None.
        """
        coords = result["most_likely_click"]  # As proportion from top, left of image
        shape = result["original_shape"]  # Dimensions of image in pixels
        # Murko returns coords as y, x
        centre_px = (coords[1] * shape[1], coords[0] * shape[0])
        LOGGER.info(f"Using image taken at {omega}, which found xtal at {centre_px}")

        beam_dist_px = calculate_beam_distance(
            (metadata["beam_centre_i"], metadata["beam_centre_j"]),
            centre_px[0],
            centre_px[1],
        )

        return camera_coordinates_to_xyz_mm(
            beam_dist_px[0],
            beam_dist_px[1],
            omega,
            metadata["microns_per_x_pixel"],
            metadata["microns_per_y_pixel"],
        )
