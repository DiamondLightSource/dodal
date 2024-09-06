import asyncio
from collections import OrderedDict
from collections.abc import Generator, Sequence
from enum import Enum
from queue import Empty, Queue
from typing import Any, TypedDict

import bluesky.plan_stubs as bps
import numpy as np
import workflows.recipe
import workflows.transport
from bluesky.protocols import Descriptor, Triggerable
from deepdiff import DeepDiff
from numpy.typing import NDArray
from ophyd_async.core import HintedSignal, StandardReadable, soft_signal_r_and_setter
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


class ZocaloSource(str, Enum):
    CPU = "CPU"
    GPU = "GPU"


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


def get_dict_differences(
    dict1: dict, dict1_source: str, dict2: dict, dict2_source: str
) -> str | None:
    """Returns dict1 and dict2 as a string if differences between them are found greater than a
    1e-5 tolerance. If dictionaries are identical, return None"""

    diff = DeepDiff(dict1, dict2, math_epsilon=1e-5, ignore_numeric_type_changes=True)

    if diff:
        return f"Zocalo results from {dict1_source} and {dict2_source} are not identical.\n Results from {dict1_source}: {dict1}\n Results from {dict2_source}: {dict2}"


def source_from_results(results):
    return (
        ZocaloSource.GPU.value
        if results["recipe_parameters"].get("gpu")
        else ZocaloSource.CPU.value
    )


class ZocaloResults(StandardReadable, Triggerable):
    """An ophyd device which can wait for results from a Zocalo job. These jobs should
    be triggered from a plan-subscribed callback using the run_start() and run_end()
    methods on dodal.devices.zocalo.ZocaloTrigger.

    See https://diamondlightsource.github.io/dodal/main/how-to/zocalo.html

    Args:
        name (str): Name of the device

        zocalo_environment (str): How zocalo is configured. Defaults to i03's development configuration

        channel (str): Name for the results Queue

        sort_key (str): How results are ranked. Defaults to sorting by highest counts

        timeout_s (float): Maximum time to wait for the Queue to be filled by an object, starting
        from when the ZocaloResults device is triggered

        prefix (str): EPICS PV prefix for the device

        use_cpu_and_gpu (bool): When True, ZocaloResults will wait for results from the CPU and the GPU, compare them, and provide a warning if the results differ. When False, ZocaloResults will only use results from the CPU

    """

    def __init__(
        self,
        name: str = "zocalo",
        zocalo_environment: str = "dev_artemis",
        channel: str = "xrc.i03",
        sort_key: str = DEFAULT_SORT_KEY.value,
        timeout_s: float = DEFAULT_TIMEOUT,
        prefix: str = "",
        use_cpu_and_gpu: bool = False,
    ) -> None:
        self.zocalo_environment = zocalo_environment
        self.sort_key = SortKeys[sort_key]
        self.channel = channel
        self.timeout_s = timeout_s
        self._prefix = prefix
        self._raw_results_received: Queue = Queue()
        self.transport: CommonTransport | None = None
        self.use_cpu_and_gpu = use_cpu_and_gpu

        self.results, self._results_setter = soft_signal_r_and_setter(
            list[XrcResult], name="results"
        )
        self.centres_of_mass, self._com_setter = soft_signal_r_and_setter(
            NDArray[np.uint64], name="centres_of_mass"
        )
        self.bbox_sizes, self._bbox_setter = soft_signal_r_and_setter(
            NDArray[np.uint64], "bbox_sizes", self.name
        )
        self.ispyb_dcid, self._ispyb_dcid_setter = soft_signal_r_and_setter(
            int, name="ispyb_dcid"
        )
        self.ispyb_dcgid, self._ispyb_dcgid_setter = soft_signal_r_and_setter(
            int, name="ispyb_dcgid"
        )
        self.add_readables(
            [
                self.results,
                self.centres_of_mass,
                self.bbox_sizes,
                self.ispyb_dcid,
                self.ispyb_dcgid,
            ],
            wrapper=HintedSignal,
        )
        super().__init__(name)

    async def _put_results(self, results: Sequence[XrcResult], recipe_parameters):
        self._results_setter(list(results))
        centres_of_mass = np.array([r["centre_of_mass"] for r in results])
        bbox_sizes = np.array([bbox_size(r) for r in results])
        self._com_setter(centres_of_mass)
        self._bbox_setter(bbox_sizes)
        self._ispyb_dcid_setter(recipe_parameters["dcid"])
        self._ispyb_dcgid_setter(recipe_parameters["dcgid"])

    def _clear_old_results(self):
        LOGGER.info("Clearing queue")
        self._raw_results_received = Queue()

    @AsyncStatus.wrap
    async def stage(self):
        """Stages the Zocalo device by: subscribing to the queue, doing a background
        sleep for a few seconds to wait for any stale messages to be received, then
        clearing the queue. Plans using this device should wait on ZOCALO_STAGE_GROUP
        before triggering processing for the experiment"""

        LOGGER.info("Subscribing to results queue")
        try:
            self._subscribe_to_results()
        except Exception as e:
            print(f"GOT {e}")
            raise

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
            source_of_first_results = source_from_results(raw_results)

            # Wait for results from CPU and GPU, warn and continue if one timed out, error if both time out
            if self.use_cpu_and_gpu:
                if source_of_first_results == ZocaloSource.CPU:
                    LOGGER.warning("Received zocalo results from CPU before GPU")
                raw_results_two_sources = [raw_results]
                try:
                    raw_results_two_sources.append(
                        self._raw_results_received.get(timeout=self.timeout_s / 2)
                    )
                    source_of_second_results = source_from_results(
                        raw_results_two_sources[1]
                    )

                    # Compare results from both sources and warn if they aren't the same
                    differences_str = get_dict_differences(
                        raw_results_two_sources[0]["results"][0],
                        source_of_first_results,
                        raw_results_two_sources[1]["results"][0],
                        source_of_second_results,
                    )
                    if differences_str:
                        LOGGER.warning(differences_str)

                except Empty:
                    source_of_missing_results = (
                        ZocaloSource.CPU.value
                        if source_of_first_results == ZocaloSource.GPU.value
                        else ZocaloSource.GPU.value
                    )
                    LOGGER.warning(
                        f"Zocalo results from {source_of_missing_results} timed out. Using results from {source_of_first_results}"
                    )

            LOGGER.info(
                f"Zocalo results from {source_of_first_results} processing: found {len(raw_results['results'])} crystals."
            )
            # Sort from strongest to weakest in case of multiple crystals
            await self._put_results(
                sorted(
                    raw_results["results"],
                    key=lambda d: d[self.sort_key.value],
                    reverse=True,
                ),
                raw_results["recipe_parameters"],
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

            if self.use_cpu_and_gpu:
                self._raw_results_received.put(
                    {"results": results, "recipe_parameters": recipe_parameters}
                )
            else:
                # Only add to queue if results are from CPU
                if not recipe_parameters.get("gpu"):
                    self._raw_results_received.put(
                        {"results": results, "recipe_parameters": recipe_parameters}
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
) -> Generator[Any, Any, tuple[np.ndarray, np.ndarray] | tuple[None, None]]:
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
