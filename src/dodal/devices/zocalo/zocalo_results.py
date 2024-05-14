import asyncio
from collections import OrderedDict
from enum import Enum
from queue import Empty, Queue
from typing import Any, Generator, Sequence, Tuple, TypedDict

import bluesky.plan_stubs as bps
import numpy as np
import workflows.recipe
import workflows.transport
from bluesky.protocols import Descriptor, Triggerable
from numpy.typing import NDArray
from ophyd_async.core import StandardReadable, soft_signal_r_and_setter
from ophyd_async.core.async_status import AsyncStatus
from workflows.transport.common_transport import CommonTransport

from dodal.devices.zocalo.zocalo_interaction import _get_zocalo_connection
from dodal.log import LOGGER


class NoResultsFromZocalo(Exception):
    pass


class NoZocaloSubscription(Exception):
    pass


class SortKeys(str, Enum):
    max_count = "max_count"
    total_count = "total_count"
    n_voxels = "n_voxels"


DEFAULT_TIMEOUT = 180
DEFAULT_SORT_KEY = SortKeys.max_count
ZOCALO_READING_PLAN_NAME = "zocalo reading"
CLEAR_QUEUE_WAIT_S = 2.0
ZOCALO_STAGE_GROUP = "clear zocalo queue"


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
        self._raw_results_received: Queue = Queue()
        self.transport: CommonTransport | None = None

        self.results, _ = soft_signal_r_and_setter(list[XrcResult], name="results")
        self.centres_of_mass, _ = soft_signal_r_and_setter(
            NDArray[np.uint64], name="centres_of_mass"
        )
        self.bbox_sizes, _ = soft_signal_r_and_setter(
            NDArray[np.uint64], "bbox_sizes", self.name
        )
        self.ispyb_dcid, _ = soft_signal_r_and_setter(int, name="ispyb_dcid")
        self.ispyb_dcgid, _ = soft_signal_r_and_setter(int, name="ispyb_dcgid")
        self.set_readable_signals(
            read=[
                self.results,
                self.centres_of_mass,
                self.bbox_sizes,
                self.ispyb_dcid,
                self.ispyb_dcgid,
            ]
        )
        super().__init__(name)

    async def _put_results(self, results: Sequence[XrcResult], ispyb_ids):
        await self.results._backend.put(list(results))
        centres_of_mass = np.array([r["centre_of_mass"] for r in results])
        bbox_sizes = np.array([bbox_size(r) for r in results])
        await self.centres_of_mass._backend.put(centres_of_mass)
        await self.bbox_sizes._backend.put(bbox_sizes)
        await self.ispyb_dcid._backend.put(ispyb_ids["dcid"])
        await self.ispyb_dcgid._backend.put(ispyb_ids["dcgid"])

    def _clear_old_results(self):
        LOGGER.info("Clearing queue")
        self._raw_results_received = Queue()

    @AsyncStatus.wrap
    async def stage(self):
        """Stages the Zocalo device by: subscribing to the queue, doing a background
        sleep for a few seconds to wait for any stale messages to be recieved, then
        clearing the queue. Plans using this device should wait on ZOCALO_STAGE_GROUP
        before triggering processing for the experiment"""

        LOGGER.info("Subscribing to results queue")
        self._subscribe_to_results()
        await asyncio.sleep(CLEAR_QUEUE_WAIT_S)
        self._clear_old_results()

    @AsyncStatus.wrap
    async def unstage(self):
        LOGGER.info("Disconnecting from Zocalo")
        if self.transport:
            self.transport.disconnect()
        self.transport = None

    @AsyncStatus.wrap
    async def trigger(self):
        """Returns an AsyncStatus waiting for results to be received from Zocalo."""
        LOGGER.info("Zocalo trigger called")
        msg = (
            "This device must be staged to subscribe to the Zocalo queue, and "
            "unstaged at the end of the experiment to avoid consuming results not "
            "meant for it"
        )
        if not self.transport:
            LOGGER.warning(
                msg  # AsyncStatus exception messages are poorly propagated, remove after https://github.com/bluesky/ophyd-async/issues/103
            )
            raise NoZocaloSubscription(msg)

        try:
            LOGGER.info(
                f"waiting for results in queue - currently {self._raw_results_received.qsize()} items"
            )

            raw_results = self._raw_results_received.get(timeout=self.timeout_s)
            LOGGER.info(f"Zocalo: found {len(raw_results)} crystals.")
            # Sort from strongest to weakest in case of multiple crystals
            await self._put_results(
                sorted(
                    raw_results["results"],
                    key=lambda d: d[self.sort_key.value],
                    reverse=True,
                ),
                raw_results["ispyb_ids"],
            )
        except Empty as timeout_exception:
            LOGGER.warning("Timed out waiting for zocalo results!")
            raise NoResultsFromZocalo(
                "Timed out waiting for Zocalo results"
            ) from timeout_exception
        finally:
            self._kickoff_run = False

    async def describe(self) -> dict[str, Descriptor]:
        zocalo_array_type: Descriptor = {
            "source": f"zocalo_service:{self.zocalo_environment}",
            "dtype": "array",
            "shape": [-1, 3],
        }
        zocalo_int_type: Descriptor = {
            "source": f"zocalo_service:{self.zocalo_environment}",
            "dtype": "integer",
            "shape": [0],
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
                (
                    self._name + "-ispyb_dcid",
                    zocalo_int_type,
                ),
                (
                    self._name + "-ispyb_dcgid",
                    zocalo_int_type,
                ),
            ],
        )

    def _subscribe_to_results(self):
        self.transport = _get_zocalo_connection(self.zocalo_environment)

        def _receive_result(
            rw: workflows.recipe.RecipeWrapper, header: dict, message: dict
        ) -> None:
            LOGGER.info(f"Received {message}")
            recipe_parameters = rw.recipe_step["parameters"]  # type: ignore # this rw is initialised with a message so recipe step is not None
            LOGGER.info(f"Recipe step parameters: {recipe_parameters}")
            self.transport.ack(header)  # type: ignore # we create transport here

            results = message.get("results", [])
            self._raw_results_received.put(
                {"results": results, "ispyb_ids": recipe_parameters}
            )

        subscription = workflows.recipe.wrap_subscribe(
            self.transport,
            self.channel,
            _receive_result,
            acknowledgement=True,
            allow_non_recipe_messages=False,
        )
        LOGGER.info(
            f"Made zocalo queue subscription: {subscription} - stored transport connection {self.transport}."
        )


def get_processing_result(
    zocalo: ZocaloResults,
) -> Generator[Any, Any, Tuple[np.ndarray, np.ndarray] | Tuple[None, None]]:
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
