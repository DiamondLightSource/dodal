import queue
from collections import deque
from datetime import datetime, timedelta
from time import sleep
from typing import Any, Optional, Sequence, TypedDict

import numpy as np
import workflows.recipe
import workflows.transport
import zocalo.configuration
from bluesky.protocols import Status, Triggerable
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


class ZocaloResults(StandardReadable, Triggerable):
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

        self.results = create_soft_signal_r(deque[XrcResult], "results", self.name)
        self.set_readable_signals(
            read=[
                self.results,
            ]
        )
        super().__init__(name)

    async def _put_results(self, results: Sequence[XrcResult]):
        await self.results._backend.put(deque(results))

    async def trigger(self) -> Status:
        await self._put_results(self._wait_for_results())
        return super().trigger()

    def _get_zocalo_connection(self):
        zc = zocalo.configuration.from_file()
        zc.activate_environment(self.zocalo_environment)

        transport = lookup("PikaTransport")()
        transport.connect()
        return transport

    def _wait_for_results(self, timeout: int | None = None) -> deque[XrcResult]:
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
                    return deque(
                        sorted(
                            raw_results, key=lambda d: d[self.sort_key], reverse=True
                        )
                    )
            raise TimeoutError(
                f"No results returned by Zocalo within timeout of {timeout} s"
            )
        finally:
            transport.disconnect()
