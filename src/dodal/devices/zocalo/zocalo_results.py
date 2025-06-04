import asyncio
from collections.abc import Generator, Sequence
from enum import Enum
from queue import Empty, Queue
from typing import Any, TypedDict

import bluesky.plan_stubs as bps
import numpy as np
import workflows.recipe
import workflows.transport
from bluesky.protocols import Triggerable
from bluesky.utils import Msg
from deepdiff.diff import DeepDiff
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_r_and_setter,
)
from workflows.transport.common_transport import CommonTransport

from dodal.devices.zocalo.zocalo_constants import ZOCALO_ENV
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
CLEAR_QUEUE_WAIT_S = 2.0
ZOCALO_STAGE_GROUP = "clear zocalo queue"


class XrcResult(TypedDict):
    """
    Information about a diffracting centre.

    NOTE: the coordinate systems of centre_of_mass and max_voxel/bounding_box are not
        the same; centre_of_mass coordinates are continuous whereas max_voxel and bounding_box
        coordinates are discrete.
    Attributes:
         centre_of_mass: The position of the centre of mass of the crystal, adjusted so that
         grid box centres lie on integer grid coordinates, such that a 1x1x1 crystal detected in
         a single grid box at 0, 0, 0, has c.o.m. of 0, 0, 0, not 0.5, 0.5, 0.5
         max_voxel: Position of the voxel with the maximum count, in integer coordinates
         max_count: max count achieved in a single voxel for the crystal
         n_voxels: Number of voxels (aka grid boxes) in the diffracting centre
         total_count: Total of above-threshold spot counts in the labelled voxels
         bounding_box: The rectangular prism that bounds the crystal, expressed
            as the volume of whole boxes as a half-open range i.e such that
            p1 = (x1, y1, z1) <= p < p2 = (x2, y2, z2) and
            p2 - p1 gives the dimensions in whole voxels.
    """

    centre_of_mass: list[float]
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
    """Returns a string containing dict1 and dict2 if there are differences between them, greater than a
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

        use_cpu_and_gpu (bool): When True, ZocaloResults will wait for results from the
        CPU and the GPU, compare them, and provide a warning if the results differ. When
        False, ZocaloResults will only use results from the CPU

        use_gpu (bool): When True, ZocaloResults will take the first set of
        results that it receives (which are likely the GPU results)

    """

    def __init__(
        self,
        name: str = "zocalo",
        zocalo_environment: str = ZOCALO_ENV,
        channel: str = "xrc.i03",
        sort_key: str = DEFAULT_SORT_KEY.value,
        timeout_s: float = DEFAULT_TIMEOUT,
        prefix: str = "",
        use_cpu_and_gpu: bool = False,
        use_gpu: bool = False,
    ) -> None:
        self.zocalo_environment = zocalo_environment
        self.sort_key = SortKeys[sort_key]
        self.channel = channel
        self.timeout_s = timeout_s
        self._prefix = prefix
        self._raw_results_received: Queue = Queue()
        self.transport: CommonTransport | None = None
        self.use_cpu_and_gpu = use_cpu_and_gpu
        self.use_gpu = use_gpu

        self.centre_of_mass, self._com_setter = soft_signal_r_and_setter(
            Array1D[np.float64], name="centre_of_mass"
        )
        self.bounding_box, self._bounding_box_setter = soft_signal_r_and_setter(
            Array1D[np.uint64], name="bounding_box"
        )
        self.max_voxel, self._max_voxel_setter = soft_signal_r_and_setter(
            Array1D[np.uint64], name="max_voxel"
        )
        self.max_count, self._max_count_setter = soft_signal_r_and_setter(
            Array1D[np.uint64], name="max_count"
        )
        self.n_voxels, self._n_voxels_setter = soft_signal_r_and_setter(
            Array1D[np.uint64], name="n_voxels"
        )
        self.total_count, self._total_count_setter = soft_signal_r_and_setter(
            Array1D[np.uint64], name="total_count"
        )
        self.ispyb_dcid, self._ispyb_dcid_setter = soft_signal_r_and_setter(
            int, name="ispyb_dcid"
        )
        self.ispyb_dcgid, self._ispyb_dcgid_setter = soft_signal_r_and_setter(
            int, name="ispyb_dcgid"
        )
        self.add_readables(
            [
                self.max_voxel,
                self.max_count,
                self.n_voxels,
                self.total_count,
                self.centre_of_mass,
                self.bounding_box,
                self.ispyb_dcid,
                self.ispyb_dcgid,
            ],
            format=StandardReadableFormat.HINTED_SIGNAL,
        )
        super().__init__(name)

    async def _put_results(self, results: Sequence[XrcResult], recipe_parameters):
        centres_of_mass = np.array([r["centre_of_mass"] for r in results])
        self._com_setter(centres_of_mass)
        self._bounding_box_setter(np.array([r["bounding_box"] for r in results]))
        self._max_voxel_setter(np.array([r["max_voxel"] for r in results]))
        self._max_count_setter(np.array([r["max_count"] for r in results]))
        self._n_voxels_setter(np.array([r["n_voxels"] for r in results]))
        self._total_count_setter(np.array([r["total_count"] for r in results]))
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

        if self.use_cpu_and_gpu and self.use_gpu:
            raise ValueError(
                "Cannot compare GPU and CPU results and use GPU results at the same time."
            )

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

            if self.use_gpu and source_of_first_results == ZocaloSource.CPU:
                LOGGER.warning(
                    "Configured to use GPU results but CPU came first, using CPU results."
                )

            if self.use_cpu_and_gpu:
                # Wait for results from CPU and GPU, warn and continue if only GPU times out. Error if CPU times out
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
                    first_results = raw_results_two_sources[0]["results"]
                    second_results = raw_results_two_sources[1]["results"]

                    if first_results and second_results:
                        # Compare results from both sources and warn if they aren't the same
                        differences_str = get_dict_differences(
                            first_results[0],
                            source_of_first_results,
                            second_results[0],
                            source_of_second_results,
                        )
                        if differences_str:
                            LOGGER.warning(differences_str)

                    # Always use CPU results
                    raw_results = (
                        raw_results_two_sources[0]
                        if source_of_first_results == ZocaloSource.CPU
                        else raw_results_two_sources[1]
                    )

                except Empty as err:
                    source_of_missing_results = (
                        ZocaloSource.CPU.value
                        if source_of_first_results == ZocaloSource.GPU.value
                        else ZocaloSource.GPU.value
                    )
                    if source_of_missing_results == ZocaloSource.GPU.value:
                        LOGGER.warning(
                            f"Zocalo results from {source_of_missing_results} timed out. Using results from {source_of_first_results}"
                        )
                    else:
                        LOGGER.error(
                            f"Zocalo results from {source_of_missing_results} timed out and GPU results not yet reliable"
                        )
                        raise err

            LOGGER.info(
                f"Zocalo results from {source_from_results(raw_results)} processing: found {len(raw_results['results'])} crystals."
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

            if self.use_cpu_and_gpu or self.use_gpu:
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


def _corrected_xrc_result(uncorrected: XrcResult) -> XrcResult:
    corrected = XrcResult(**uncorrected)
    corrected["centre_of_mass"] = [
        coord - 0.5 for coord in uncorrected["centre_of_mass"]
    ]
    return corrected


def get_full_processing_results(
    zocalo: ZocaloResults,
) -> Generator[Msg, Any, Sequence[XrcResult]]:
    """A plan that will return the raw zocalo results, ranked in descending order according to the sort key.
    Returns empty list in the event no results found."""
    LOGGER.info("Retrieving raw zocalo processing results")
    com = yield from bps.rd(zocalo.centre_of_mass, default_value=[])
    max_voxel = yield from bps.rd(zocalo.max_voxel, default_value=[])
    max_count = yield from bps.rd(zocalo.max_count, default_value=[])
    n_voxels = yield from bps.rd(zocalo.n_voxels, default_value=[])
    total_count = yield from bps.rd(zocalo.total_count, default_value=[])
    bounding_box = yield from bps.rd(zocalo.bounding_box, default_value=[])
    return [
        _corrected_xrc_result(
            XrcResult(
                centre_of_mass=com.tolist(),
                max_voxel=mv.tolist(),
                max_count=int(mc),
                n_voxels=int(n),
                total_count=int(tc),
                bounding_box=bb.tolist(),
            )
        )
        for com, mv, mc, n, tc, bb in zip(
            com, max_voxel, max_count, n_voxels, total_count, bounding_box, strict=True
        )
    ]
