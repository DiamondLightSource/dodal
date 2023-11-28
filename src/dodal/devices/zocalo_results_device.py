import queue
from collections import OrderedDict
from datetime import datetime, timedelta
from time import sleep
from typing import Any, Optional, TypedDict

import numpy as np
import workflows.recipe
import workflows.transport
import zocalo.configuration
from bluesky.protocols import Reading
from numpy.typing import NDArray
from ophyd_async.core import StandardReadable
from workflows.transport import lookup

from dodal.devices.ophyd_async_utils import create_soft_signal_r
from dodal.log import LOGGER

SORT_KEY = "max_count"
TIMEOUT = 15


class XrcResult(TypedDict):
    centre_of_mass: list[int]
    max_voxel: list[int]
    max_count: int
    n_voxels: int
    total_count: int
    bounding_box: list[list[int]]


NULL_RESULT: XrcResult = {
    "centre_of_mass": [0],
    "max_voxel": [0],
    "max_count": 0,
    "n_voxels": 0,
    "total_count": 0,
    "bounding_box": [[0]],
}


def parse_reading(reading: dict[str, Any], name: str = "zocalo_results") -> XrcResult:
    return {
        "centre_of_mass": list(reading[f"{name}-centre_of_mass"]["value"]),
        "max_voxel": list(reading[f"{name}-max_voxel"]["value"]),
        "max_count": reading[f"{name}-max_count"]["value"],
        "n_voxels": reading[f"{name}-n_voxels"]["value"],
        "total_count": reading[f"{name}-total_count"]["value"],
        "bounding_box": [list(p) for p in reading[f"{name}-bounding_box"]["value"]],
    }


class ZocaloResults(StandardReadable):
    """An ophyd device which can wait for results from a Zocalo job"""

    def __init__(
        self,
        zocalo_environment: str,
        channel: str = "xrc.i03",
        name: str = "zocalo_results",
        sort_key: str = SORT_KEY,
    ) -> None:
        self.zocalo_environment = zocalo_environment
        self.sort_key = sort_key
        self.channel = channel
        self.results: list[XrcResult] = []

        self.centre_of_mass = create_soft_signal_r(
            NDArray[np.uint], "centre_of_mass", self.name
        )
        self.max_voxel = create_soft_signal_r(NDArray[np.uint], "max_voxel", self.name)
        self.max_count = create_soft_signal_r(int, "max_count", self.name)
        self.n_voxels = create_soft_signal_r(int, "n_voxels", self.name)
        self.total_count = create_soft_signal_r(int, "total_count", self.name)
        self.bounding_box = create_soft_signal_r(
            NDArray[np.uint], "bounding_box", self.name
        )
        self.set_readable_signals(
            read=[
                self.centre_of_mass,
                self.max_voxel,
                self.max_count,
                self.n_voxels,
                self.total_count,
                self.bounding_box,
            ]
        )
        super().__init__(name)

    async def read(self) -> dict[str, Reading]:
        if self.results == []:
            self.results = self._wait_for_results()
        await self._put_result(
            self.results.pop(0) if self.results != [] else NULL_RESULT
        )
        return await super().read()

    async def _put_result(self, result: XrcResult):
        await self.centre_of_mass._backend.put(np.array(result["centre_of_mass"]))
        await self.max_voxel._backend.put(np.array(result["max_voxel"]))
        await self.max_count._backend.put(result["max_count"])
        await self.n_voxels._backend.put(result["n_voxels"])
        await self.total_count._backend.put(result["total_count"])
        await self.bounding_box._backend.put(np.array(result["bounding_box"]))

    def _get_zocalo_connection(self):
        zc = zocalo.configuration.from_file()
        zc.activate_environment(self.zocalo_environment)

        transport = lookup("PikaTransport")()
        transport.connect()
        return transport

    def _wait_for_results(self, timeout: int | None = None) -> list[XrcResult]:
        """Block until a result is received from Zocalo.
        Args:
            data_collection_group_id (int): The ID of the data collection group representing
                                            the gridscan in ISPyB

            timeout (float): The time in seconds to wait for the result to be received.
        Returns:
            Returns the message from zocalo, as a list of dicts describing each crystal
            which zocalo found:
            {
                "results": [
                    {
                        "centre_of_mass": [1, 2, 3],
                        "max_voxel": [2, 4, 5],
                        "max_count": 105062,
                        "n_voxels": 35,
                        "total_count": 2387574,
                        "bounding_box": [[1, 2, 3], [3, 4, 4]],
                    },
                    {
                        result 2
                    },
                    ...
                ]
            }
        """
        # Set timeout default like this so that we can modify TIMEOUT during tests
        if timeout is None:
            timeout = TIMEOUT
        transport = self._get_zocalo_connection()
        result_received: queue.Queue = queue.Queue()
        exception: Optional[Exception] = None

        def _receive_result(
            rw: workflows.recipe.RecipeWrapper, header: dict, message: dict
        ) -> None:
            try:
                LOGGER.info(f"Received {message}")
                recipe_parameters = rw.recipe_step["parameters"]  # type: ignore # this rw is initialised with a message so recipe step is not None
                LOGGER.info(f"Recipe step parameters: {recipe_parameters}")
                transport.ack(header)

                results = message.get("results", [])
                result_received.put(results)
            except Exception as e:
                nonlocal exception
                exception = e
                raise e

        workflows.recipe.wrap_subscribe(
            transport,
            self.channel,
            _receive_result,
            acknowledgement=True,
            allow_non_recipe_messages=False,
        )

        try:
            start_time = datetime.now()
            while datetime.now() - start_time < timedelta(seconds=timeout):
                if result_received.empty():
                    if exception is not None:
                        raise exception  # type: ignore # exception is not Never, it can be set in receive_result
                    else:
                        sleep(0.1)
                else:
                    raw_results = result_received.get_nowait()
                    LOGGER.info(f"Zocalo: found {len(raw_results)} crystals.")
                    # Sort from strongest to weakest in case of multiple crystals
                    return sorted(
                        raw_results, key=lambda d: d[self.sort_key], reverse=True
                    )
            raise TimeoutError(
                f"No results returned by Zocalo within timeout of {timeout} s"
            )
        finally:
            transport.disconnect()
