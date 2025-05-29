import json
import pickle
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

from dodal.devices.i04.constants import RedisConstants
from dodal.devices.oav.oav_calculations import (
    calculate_beam_distance,
)
from dodal.log import LOGGER

NO_MURKO_RESULT = (-1, -1)

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
    """Device that takes crystal centre values from Murko and uses them to set the
    x, y, z coordinate of the sample to be in line with the beam centre.
    The most_likely_click[1] value from Murko corresponds with the x coordinate of the
    sample. The most_likely_click[0] value from Murko corresponds with a component of
    the y and z coordinates of the sample, depending on the omega angle, as the sample
    is rotated around the x axis.

    Given a most_likely_click value at a certain omega angle θ:
    most_likely_click[1] = x
    most_likely_click[0] = cos(θ)y - sin(θ)z

    A value for x can be found by averaging all most_likely_click[1] values, and
    solutions for y and z can be calculated using numpy's linear algebra library.
    """

    TIMEOUT_S = 2

    def __init__(
        self,
        redis_host=RedisConstants.REDIS_HOST,
        redis_password=RedisConstants.REDIS_PASSWORD,
        redis_db=RedisConstants.MURKO_REDIS_DB,
        name="",
        stop_angle=350,
    ):
        self.redis_client = StrictRedis(
            host=redis_host,
            password=redis_password,
            db=redis_db,
        )
        self.pubsub = self.redis_client.pubsub()
        self._last_omega = 0
        self.sample_id = soft_signal_rw(str)  # Should get from redis
        self.stop_angle = stop_angle
        self.x_dists_mm = []
        self.y_dists_mm = []
        self.omegas = []

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
            # waits here for next batch to be received
            message = await self.pubsub.get_message(timeout=self.TIMEOUT_S)
            if message is None:  # No more messages to process
                break
            await self.process_batch(message, sample_id)

        for i in range(len(self.omegas)):
            LOGGER.debug(
                f"omega: {round(self.omegas[i], 2)}, x: {round(self.x_dists_mm[i], 2)}, y: {round(self.y_dists_mm[i], 2)}"
            )

        LOGGER.info(f"Using average of x beam distances: {self.x_dists_mm}")
        avg_x = float(np.mean(self.x_dists_mm))
        LOGGER.info(f"Finding least square y and z from y distances: {self.y_dists_mm}")
        best_y, best_z = get_yz_least_squares(self.y_dists_mm, self.omegas)
        # x, y, z are relative to beam centre. Need to move negative these values to get centred.
        self._x_mm_setter(-avg_x)
        self._y_mm_setter(-best_y)
        self._z_mm_setter(-best_z)

    async def process_batch(self, message: dict | None, sample_id: str):
        if message and message["type"] == "message":
            batch_results: list[dict] = pickle.loads(message["data"])
            for results in batch_results:
                for uuid, result in results.items():
                    if metadata_str := await self.redis_client.hget(  # type: ignore
                        f"murko:{sample_id}:metadata", uuid
                    ):
                        LOGGER.info(
                            f"Found metadata for uuid {uuid}, processing result"
                        )
                        self.process_result(
                            result, MurkoMetadata(json.loads(metadata_str))
                        )
                    else:
                        LOGGER.info(f"Found no metadata for uuid {uuid}")

    def process_result(self, result: dict, metadata: MurkoMetadata):
        """Uses the 'most_likely_click' coordinates from Murko to calculate the
        horizontal and vertical distances from the beam centre, and store these values
        as well as the omega angle the image was taken at.
        """
        omega = metadata["omega_angle"]
        coords = result["most_likely_click"]  # As proportion from top, left of image
        LOGGER.info(f"Got most_likely_click: {coords} at angle {omega}")
        if (
            tuple(coords) == NO_MURKO_RESULT
        ):  # See https://github.com/MartinSavko/murko/issues/9
            LOGGER.info("Murko didn't produce a result, moving on")
        else:
            shape = result["original_shape"]  # Dimensions of image in pixels
            # Murko returns coords as y, x
            centre_px = (coords[1] * shape[1], coords[0] * shape[0])

            beam_dist_px = calculate_beam_distance(
                (metadata["beam_centre_i"], metadata["beam_centre_j"]),
                centre_px[0],
                centre_px[1],
            )
            self.x_dists_mm.append(
                beam_dist_px[0] * metadata["microns_per_x_pixel"] / 1000
            )
            self.y_dists_mm.append(
                beam_dist_px[1] * metadata["microns_per_y_pixel"] / 1000
            )
            self.omegas.append(omega)
            self._last_omega = omega


def get_yz_least_squares(vertical_dists: list, omegas: list) -> tuple[float, float]:
    """Get the least squares solution for y and z from the vertical distances and omega angles.

    Args:
        v_dists (list): List of vertical distances from beam centre. Any units
        omegas (list): List of omega angles in degrees.

    Returns:
        tuple[float, float]: y, z distances from centre, in whichever units
        v_dists came as.
    """
    thetas = np.radians(omegas)
    matrix = np.column_stack([np.cos(thetas), -np.sin(thetas)])

    yz, residuals, rank, s = np.linalg.lstsq(matrix, vertical_dists, rcond=None)
    y, z = yz
    return y, z
