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

    Given a most_liekly_click value at a certain omega angle θ:
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
            # waits here for next batch to be recieved
            message = await self.pubsub.get_message(timeout=self.TIMEOUT_S)
            if message is None:  # No more messages to process
                break
            await self.process_batch(message, sample_id)
        LOGGER.info(f"Using average of x beam distances: {self.x_dists_mm}")
        avg_x = float(np.mean(self.x_dists_mm))
        LOGGER.info(f"Finding least square y and z from y distances: {self.y_dists_mm}")
        best_y, best_z = self.get_yz_least_squares(self.y_dists_mm, self.omegas)
        self._x_mm_setter(avg_x)
        self._y_mm_setter(best_y)
        self._z_mm_setter(best_z)

    async def process_batch(self, message: dict | None, sample_id: str):
        if message and message["type"] == "message":
            batch_results = pickle.loads(message["data"])
            for results in batch_results:
                LOGGER.info(f"Got {results} from redis")
                for uuid, result in results.items():
                    if metadata_str := await self.redis_client.hget(  # type: ignore
                        f"murko:{sample_id}:metadata", uuid
                    ):
                        self.process_result(result, uuid, metadata_str)

    def process_result(self, result: dict, uuid: int, metadata_str: str):
        """Uses the 'most_likely_click' coordinates from Murko to calculate the
        horizontal and vertical distances from the beam centre, and store these values
        as well as the omega angle the image was taken at.
        """
        LOGGER.info(f"Using result {uuid}, {metadata_str}, {result}")
        metadata = MurkoMetadata(json.loads(metadata_str))
        omega = metadata["omega_angle"]
        LOGGER.info(f"Got angle {omega}")
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
        LOGGER.info(f"Found horizontal distance at {beam_dist_px[0]}, angle = {omega}")
        LOGGER.info(f"Found vertical distance at {beam_dist_px[1]}, angle = {omega}")
        self.x_dists_mm.append(
            -beam_dist_px[0] * metadata["microns_per_x_pixel"] / 1000
        )
        self.y_dists_mm.append(
            -beam_dist_px[1] * metadata["microns_per_y_pixel"] / 1000
        )
        self.omegas.append(omega)

    @staticmethod
    def get_yz_least_squares(v_values: list, omegas: list) -> tuple[float, float]:
        """Get the least squares solution for y and z from the vertical distances and omega angles.

        Args:
            v_values (list): List of vertical distances from beam centre in mm.
            thetas_deg (list): List of omega angles in degrees.

        Returns:
            tuple[float, float]: y, z coordinates
        """
        thetas = np.radians(omegas)
        matrix = np.column_stack([np.cos(thetas), -np.sin(thetas)])

        yz, residuals, rank, s = np.linalg.lstsq(matrix, v_values, rcond=None)
        y, z = yz
        return y, z
