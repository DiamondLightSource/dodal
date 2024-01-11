from collections import OrderedDict
from enum import Enum
from queue import Empty, Queue
from typing import Any, Generator, Sequence, Tuple, TypedDict, Union

import bluesky.plan_stubs as bps
import numpy as np
import workflows.recipe
import workflows.transport
from bluesky.protocols import Descriptor, Triggerable
from numpy.typing import NDArray
from ophyd_async.core import StandardReadable
from ophyd_async.core.async_status import AsyncStatus

from dodal.devices.ophyd_async_utils import create_soft_signal_r
from dodal.devices.zocalo.zocalo_interaction import _get_zocalo_connection
from dodal.log import LOGGER

DEFAULT_TIMEOUT = 180


class NoResultsFromZocalo(Exception):
    pass


class SortKeys(str, Enum):
    max_count = "max_count"
    total_count = "total_count"
    n_voxels = "n_voxels"


DEFAULT_SORT_KEY = SortKeys.max_count
ZOCALO_READING_PLAN_NAME = "zocalo reading"


class XrcResult(TypedDict):
    centre_of_mass: list[int]
    max_voxel: list[int]
    max_count: int
    n_voxels: int
    total_count: int
    bounding_box: list[list[int]]


def bbox_size(result: XrcResult):
    return [
        abs(result["bounding_box"][1][i] - result["bounding_box"][0][i])
        for i in range(3)
    ]


class ZocaloResults(StandardReadable, Triggerable):
    """An ophyd device which can wait for results from a Zocalo job. These jobs should
    be triggered from a plan-subscribed callback using the run_start() and run_end()
    methods on dodal.devices.zocalo.ZocaloTrigger.

    See https://github.com/DiamondLightSource/dodal/wiki/How-to-Interact-with-Zocalo"""

    def __init__(
        self,
        name: str = "zocalo",
        zocalo_environment: str = "dev_artemis",
        channel: str = "xrc.i03",
        sort_key: str = DEFAULT_SORT_KEY.value,
        timeout_s: float = DEFAULT_TIMEOUT,
        prefix: str = "",
    ) -> None:
        self.zocalo_environment = zocalo_environment
        self.sort_key = SortKeys[sort_key]
        self.channel = channel
        self.timeout_s = timeout_s
        self._prefix = prefix

        self._subscription_run: bool = False
        self._raw_results_received: Queue = Queue()

        self.results = create_soft_signal_r(list[XrcResult], "results", self.name)
        self.centres_of_mass = create_soft_signal_r(
            NDArray[np.uint64], "centres_of_mass", self.name
        )
        self.bbox_sizes = create_soft_signal_r(
            NDArray[np.uint64], "bbox_sizes", self.name
        )
        self.set_readable_signals(
            read=[
                self.results,
                self.centres_of_mass,
                self.bbox_sizes,
            ]
        )
        super().__init__(name)

    async def _put_results(self, results: Sequence[XrcResult]):
        await self.results._backend.put(list(results))
        centres_of_mass = np.array([r["centre_of_mass"] for r in results])
        bbox_sizes = np.array([bbox_size(r) for r in results])
        await self.centres_of_mass._backend.put(centres_of_mass)
        await self.bbox_sizes._backend.put(bbox_sizes)

    @AsyncStatus.wrap
    async def trigger(self):
        """Returns an AsyncStatus waiting for results to be received from Zocalo."""
        LOGGER.info("Zocalo trigger called")
        if not self._subscription_run:
            LOGGER.info("subscription not initialised, subscribing to queue")
            self._subscribe_to_results()
            self._subscription_run = True

        try:
            LOGGER.info("waiting for results in queue")

            raw_results = self._raw_results_received.get(timeout=self.timeout_s)
            LOGGER.info(f"Zocalo: found {len(raw_results)} crystals.")
            # Sort from strongest to weakest in case of multiple crystals
            await self._put_results(
                sorted(raw_results, key=lambda d: d[self.sort_key.value], reverse=True)
            )
        except Empty as timeout_exception:
            LOGGER.warning("Timed out waiting for zocalo results!")
            raise NoResultsFromZocalo() from timeout_exception
        finally:
            self._kickoff_run = False

    async def describe(self) -> dict[str, Descriptor]:
        zocalo_array_type: Descriptor = {
            "source": f"zocalo_service:{self.zocalo_environment}",
            "dtype": "array",
            "shape": [-1, 3],
        }
        return OrderedDict(
            [
                (
                    self._name + "-results",
                    {
                        "source": f"zocalo_service:{self.zocalo_environment}",
                        "dtype": "array",
                        "shape": [
                            -1,
                        ],  # TODO describe properly - see https://github.com/DiamondLightSource/dodal/issues/253
                    },
                ),
                (
                    self._name + "-centres_of_mass",
                    zocalo_array_type,
                ),
                (
                    self._name + "-bbox_sizes",
                    zocalo_array_type,
                ),
            ],
        )

    def _subscribe_to_results(self):
        transport = _get_zocalo_connection(self.zocalo_environment)

        def _receive_result(
            rw: workflows.recipe.RecipeWrapper, header: dict, message: dict
        ) -> None:
            LOGGER.info(f"Received {message}")
            recipe_parameters = rw.recipe_step["parameters"]  # type: ignore # this rw is initialised with a message so recipe step is not None
            LOGGER.info(f"Recipe step parameters: {recipe_parameters}")
            transport.ack(header)

            results = message.get("results", [])
            self._raw_results_received.put(results)

        subscription = workflows.recipe.wrap_subscribe(
            transport,
            self.channel,
            _receive_result,
            acknowledgement=True,
            allow_non_recipe_messages=False,
        )
        LOGGER.info(f"Made zocalo queue subscription: {bool(subscription)}.")


def get_processing_result(
    zocalo: ZocaloResults,
) -> Generator[Any, Any, Union[Tuple[np.ndarray, np.ndarray], Tuple[None, None]]]:
    """A minimal plan which will extract the top ranked xray centre and crystal bounding
    box size from the zocalo results. Returns (None, None) if no crystals were found."""

    LOGGER.info("Getting zocalo processing results.")
    centres_of_mass = yield from bps.rd(zocalo.centres_of_mass, default_value=[])  # type: ignore
    LOGGER.debug(f"Centres of mass: {centres_of_mass}")
    centre_of_mass = (
        None
        if len(centres_of_mass) == 0  # type: ignore
        else centres_of_mass[0] - np.array([0.5, 0.5, 0.5])  # type: ignore
    )
    LOGGER.debug(f"Adjusted top centring result: {centre_of_mass}")
    bbox_sizes = yield from bps.rd(zocalo.bbox_sizes, default_value=[])  # type: ignore
    LOGGER.debug(f"Bounding box sizes: {centres_of_mass}")
    bbox_size = None if len(bbox_sizes) == 0 else bbox_sizes[0]  # type: ignore
    LOGGER.debug(f"Top bbox size: {bbox_size}")
    return centre_of_mass, bbox_size
