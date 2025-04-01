import json
import os
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
from redis import StrictRedis

# from dodal.beamlines.i04 import MURKO_REDIS_DB, REDIS_HOST, REDIS_PASSWORD
from dodal.devices.oav.oav_calculations import (
    calculate_beam_distance,
    camera_coordinates_to_xyz_mm,
)
from dodal.log import LOGGER

REDIS_HOST = os.environ.get("VALKEY_PROD_SVC_SERVICE_HOST", "test_redis")
REDIS_PASSWORD = os.environ.get("VALKEY_PASSWORD", "test_redis_password")
MURKO_REDIS_DB = 7

MurkoResult = dict
FullMurkoResults = dict[str, list[MurkoResult]]


class MurkoMetadata(TypedDict):
    zoom_percentage: float
    microns_per_x_pixel: float
    microns_per_y_pixel: float
    beam_centre_i: float
    beam_centre_j: float
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
        prefix="",
        redis_host=REDIS_HOST,
        redis_password=REDIS_PASSWORD,
        db=MURKO_REDIS_DB,
        name="",
    ):
        self.redis_client = StrictRedis(
            host=redis_host,
            password=redis_password,
            db=db,
        )
        self.pubsub = self.redis_client.pubsub()
        self._last_omega = 0
        self._last_result = None
        self.sample_id = soft_signal_rw(str)  # Should get from redis
        self.coords = {"x": {}, "y": {}, "z": {}}
        self.search_angles = OrderedDict(
            [  # Angles to search and dimensions to gather at each angle
                (90, ("x", "z")),
                (180, ("x", "y")),
                (270, ()),  # Stop searching here
            ]
        )
        self.angles_to_search = list(self.search_angles.keys())

        with self.add_children_as_readables():
            # Diffs from current x/y/z
            self.x_mm, self._x_mm_setter = soft_signal_r_and_setter(float)
            self.y_mm, self._y_mm_setter = soft_signal_r_and_setter(float)
            self.z_mm, self._z_mm_setter = soft_signal_r_and_setter(float)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def stage(self):
        # Subscribe to redis pub/
        await self.pubsub.subscribe("murko-results")
        self._x_mm_setter(None)
        self._y_mm_setter(None)
        self._z_mm_setter(None)

    @AsyncStatus.wrap
    async def unstage(self):
        # Unsubscribe
        await self.pubsub.unsubscribe()

    def get_beam_centre(self) -> tuple[int, int]:
        return (442, 363)

    def get_coords_if_at_angle(
        self,
        metadata: MurkoMetadata,
        result: MurkoResult,
        omega: float,
        search_angle: float,
    ) -> np.ndarray | None:
        LOGGER.info(f"Compare {omega}, {search_angle}, {self._last_omega}")
        if (  # if last omega is closest
            abs(omega - search_angle) >= abs(self._last_omega - search_angle)
            and self._last_result is not None
        ):
            closest_result = self._last_result
            closest_omega = self._last_omega
        elif omega - search_angle >= 0:  # if this omega is closest
            closest_result = result
            closest_omega = omega
        else:
            return None
        coords = closest_result[
            "most_likely_click"
        ]  # As proportion from top, left of image
        shape = closest_result["original_shape"]  # Dimensions of image in pixels
        # Murko returns coords as y, x
        centre_px = (coords[1] * shape[1], coords[0] * shape[0])
        LOGGER.info(
            f"Using image taken at {closest_omega}, which found xtal at {centre_px}"
        )

        beam_dist_px = calculate_beam_distance(
            self.get_beam_centre(),  # beam centre
            centre_px[0],
            centre_px[1],
        )

        return camera_coordinates_to_xyz_mm(
            beam_dist_px[0],
            beam_dist_px[1],
            closest_omega,
            metadata["microns_per_x_pixel"],
            metadata["microns_per_y_pixel"],
        )

    @AsyncStatus.wrap
    async def trigger(self):
        # May be better as kickoff/complete?
        # Wait for results
        sample_id = await self.sample_id.get_value()
        next_angle = self.angles_to_search.pop(0)
        final_message = None
        while next_angle:  # Goes round in a loop until 270 degrees is found
            # waits here for next batch to be recieved (10 scans?). pickle deserialises data
            message = await self.pubsub.get_message(timeout=self.TIMEOUT_S)
            if message is None:  # No more messages to process
                await self.process_batch(
                    final_message, sample_id, next_angle
                )  # Process final message again
                break
            next_angle = await self.process_batch(message, sample_id, next_angle)
            final_message = message
        x_values = list(self.coords["x"].values())
        y_values = list(self.coords["y"].values())
        z_values = list(self.coords["z"].values())
        assert x_values, "No x values"
        assert z_values, "No z values"
        assert y_values, "No y values"
        self._x_mm_setter(np.mean(x_values))
        self._y_mm_setter(np.mean(y_values))
        self._z_mm_setter(np.mean(z_values))

    async def process_batch(self, message, sample_id, next_angle):
        if message and message["type"] == "message":
            batch_results = pickle.loads(message["data"])
            for results in batch_results:
                print(f"Got {results} from redis")
                assert isinstance(results, dict)
                for uuid, result in results.items():
                    if metadata_str := await self.redis_client.hget(
                        f"murko:{sample_id}:metadata", uuid
                    ):
                        next_angle = self.process_result(
                            result, uuid, metadata_str, next_angle
                        )
        return next_angle

    def process_result(
        self, result: dict, uuid: int, metadata_str: str, search_angle: float | None
    ) -> float:
        if search_angle is None:
            return None
        metadata = MurkoMetadata(json.loads(metadata_str))
        omega_angle = metadata["omega_angle"]
        assert search_angle, f"search_angle = {search_angle}"
        LOGGER.info(f"Got angle {omega_angle}")
        # Find closest to next search angle
        if (
            movement := self.get_coords_if_at_angle(
                metadata, result, omega_angle, search_angle
            )
        ) is not None:
            LOGGER.info(f"Using result {uuid}, {metadata_str}, {result}")
            for coord in self.search_angles[search_angle]:
                self.coords[coord][omega_angle] = movement[Coord[coord].value]
            if self.angles_to_search:
                search_angle = self.angles_to_search.pop(0)
            else:
                search_angle = None
            LOGGER.info(f"Setting {search_angle} to {movement}")
        self._last_omega = omega_angle
        self._last_result = result
        return search_angle
