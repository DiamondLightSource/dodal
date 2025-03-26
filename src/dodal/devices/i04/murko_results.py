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
from redis.asynio import StrictRedis

from dodal.beamlines.i04 import MURKO_REDIS_DB, REDIS_HOST, REDIS_PASSWORD
from dodal.devices.oav.oav_calculations import (
    calculate_beam_distance,
    camera_coordinates_to_xyz,
)
from dodal.log import LOGGER

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
        self.sample_id = soft_signal_rw(str)  # Should get from redis
        self.coords = {"x": {}, "y": {}, "z": {}}
        self.search_angles = OrderedDict(
            [(90, ("x", "z")), (180, ("x", "y")), (270, ())]
        )
        self.angles_to_search = list(self.search_angles.keys())
        self.current_x_y_z_um = soft_signal_rw(
            tuple[float, float, float]
        )  # Should get from redis

        with self.add_children_as_readables():
            # Diffs from current x/y/z
            self.x_um, self._x_um_setter = soft_signal_r_and_setter(float)
            self.y_um, self._y_um_setter = soft_signal_r_and_setter(float)
            self.z_um, self._z_um_setter = soft_signal_r_and_setter(float)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def stage(self):
        # Subscribe to redis pub/
        await self.pubsub.subscribe("murko-results")
        self._x_um_setter(None)
        self._y_um_setter(None)
        self._z_um_setter(None)

    @AsyncStatus.wrap
    async def unstage(self):
        # Unsubscribe
        await self.pubsub.unsubscribe()

    def get_coords_if_at_angle(
        self,
        metadata: MurkoMetadata,
        result: MurkoResult,
        omega: float,
        search_angle: float,
    ) -> np.ndarray | None:
        LOGGER.info(f"Compare {omega}, {search_angle}, {self._last_omega}")
        if abs(omega - search_angle) > abs(self._last_omega - search_angle):
            coords = result[
                "most_likely_click"
            ]  # As proportion from top, left of image
            shape = result["original_shape"]  # Dimensions of image in pixels
            centre_px = (coords[1] * shape[1], coords[0] * shape[0])
            LOGGER.info(
                f"Using image taken at {omega}, which found xtal at {centre_px}"
            )

            beam_dist_px = calculate_beam_distance(
                (442, 363),
                centre_px[0],
                centre_px[1],  # Not sure where this number comes from
            )

            return camera_coordinates_to_xyz(
                beam_dist_px[0],
                beam_dist_px[1],
                omega,
                metadata["microns_per_x_pixel"],
                metadata["microns_per_y_pixel"],
            )
        return None

    @AsyncStatus.wrap
    async def trigger(self):
        # May be better as kickoff/complete?
        # Wait for results
        sample_id = await self.sample_id.get_value()
        next_angle = self.angles_to_search.pop(0)
        while next_angle:  # Goes round in a loop until 270 degrees is found
            message = await self.pubsub.get_message(timeout=self.TIMEOUT_S)
            if message and message["type"] == "message":
                batch_results = pickle.loads(
                    message["data"]
                )  # waits here for next batch to be recieved (10 scans?). pickle deserialises results
                for results in batch_results:
                    print(f"Got {results} from redis")
                    assert isinstance(results, dict)
                    for uuid, result in results.items():
                        metadata_str = await self.redis_client.hget(
                            f"murko:{sample_id}:metadata", uuid
                        )
                        if metadata_str:
                            next_angle = self.process_result(
                                result, uuid, metadata_str, next_angle
                            )
        self._x_um_setter(np.mean(self.coords["x"].values()))
        self._y_um_setter(np.mean(self.coords["y"].values()))
        self._z_um_setter(np.mean(self.coords["z"].values()))

    def process_result(self, result: dict, uuid, metadata_str, angle):
        metadata = MurkoMetadata(
            json.loads(metadata_str)
        )  # Metadata is JSON but data is pickle?
        omega_angle = metadata["omega_angle"]
        LOGGER.info(f"Got angle {omega_angle}")
        # Find closest to next search angle
        if (
            movement := self.get_coords_if_at_angle(
                metadata, result, omega_angle, angle
            )
        ) is not None:
            LOGGER.info(f"Using result {uuid}, {metadata_str}, {result}")
            for coord in self.search_angles[angle]:
                self.coords[coord][omega_angle] = movement[Coord[coord].value]
            if self.angles_to_search:
                angle = self.angles_to_search.pop(0)
            else:
                angle = None
            LOGGER.info(f"Setting {angle} to {movement}")
        self._last_omega = omega_angle
        return angle
