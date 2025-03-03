import json
import pickle
from typing import TypedDict

from bluesky.protocols import Stageable, Triggerable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from redis import StrictRedis

from dodal.beamlines.i04 import MURKO_REDIS_DB, REDIS_HOST, REDIS_PASSWORD
from dodal.devices.oav.oav_calculations import camera_coordinates_to_xyz
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
        self.found_90 = False
        self.current_x_y_z_um = soft_signal_rw(
            tuple[float, float, float]
        )  # Should get from redis

        with self.add_children_as_readables():
            # Diffs from current x/y/z
            self.x_um, self._x_um_setter = soft_signal_r_and_setter(float | None)
            self.y_um, self._y_um_setter = soft_signal_r_and_setter(float | None)
            self.z_um, self._z_um_setter = soft_signal_r_and_setter(float | None)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def stage(self):
        # Subscribe to redis pub/
        self.pubsub.subscribe("murko-results")
        self._x_um_setter(None)
        self._y_um_setter(None)
        self._z_um_setter(None)

    @AsyncStatus.wrap
    async def unstage(self):
        # Unsubscribe
        self.pubsub.unsubscribe()

    def get_coords_if_at_angle(
        self,
        metadata: MurkoMetadata,
        result: MurkoResult,
        omega: float,
        search_angle: float,
    ):
        if abs(omega - search_angle) > abs(self._last_omega - search_angle):
            coords = result["most_likely_click"]
            shape = result["original_image_shape"]
            centre_px = (coords[1] * shape[1], coords[0] * shape[0])
            LOGGER.info(
                f"Using image taken at {omega}, which found xtal at {centre_px}"
            )

            return camera_coordinates_to_xyz(
                centre_px[0],
                centre_px[1],
                omega,
                metadata["microns_per_x_pixel"],
                metadata["microns_per_y_pixel"],
            )
        return None

    @AsyncStatus.wrap
    async def trigger(self):
        # May be better as kickoff/complete?
        # Wait for results
        sample_id = self.sample_id.get_value()
        while not self.z_um.get_value():
            message = self.pubsub.get_message(timeout=self.TIMEOUT_S)
            results = pickle.loads(message)
            assert isinstance(results, FullMurkoResults)
            # Get metadata
            for uuid, result in results:
                metadata_str = self.redis_client.hget(
                    f"murko:{sample_id}:metadata", uuid
                )
                LOGGER.info(f"Got result {uuid}, {metadata_str}, {result}")
                metadata = MurkoMetadata(json.loads(metadata_str))
                omega_angle = metadata["omega_angle"]
                if not self.y_um.get_value():
                    # Find closest to 90
                    if movement := self.get_coords_if_at_angle(
                        metadata, result, omega_angle, 90
                    ):
                        self._x_um_setter(movement[0])
                        self._y_um_setter(movement[1])
                else:
                    if movement := self.get_coords_if_at_angle(
                        metadata, result, omega_angle, 180
                    ):
                        self._x_um_setter(movement[0])
                        self._z_um_setter(movement[2])

                self._last_omega = omega_angle
