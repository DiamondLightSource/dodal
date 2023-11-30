import asyncio
from collections import OrderedDict
from typing import Any, Generator, Sequence, Tuple, TypedDict, Union

import bluesky.plan_stubs as bps
import numpy as np
import workflows.recipe
import workflows.transport
import zocalo.configuration
from bluesky.protocols import Descriptor, Flyable
from bluesky.run_engine import call_in_bluesky_event_loop
from ophyd.status import Status
from ophyd_async.core import StandardReadable
from ophyd_async.core.async_status import AsyncStatus
from workflows.transport import lookup

from dodal.devices.ophyd_async_utils import create_soft_signal_r
from dodal.log import LOGGER

DEFAULT_SORT_KEY = "max_count"
DEFAULT_TIMEOUT = 180


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


class ZocaloResults(StandardReadable, Flyable):
    """An ophyd device which can wait for results from a Zocalo job"""

    def __init__(
        self,
        name: str = "zocalo_results",
        zocalo_environment: str = "dev_artemis",
        channel: str = "xrc.i03",
        sort_key: str = DEFAULT_SORT_KEY,
        timeout_s: float = DEFAULT_TIMEOUT,
        prefix: str = "",
    ) -> None:
        self.zocalo_environment = zocalo_environment
        self.sort_key = sort_key
        self.channel = channel
        self.timeout_s = timeout_s
        self._prefix = prefix

        self._kickoff_run: bool
        self._raw_results_received: asyncio.Queue = asyncio.Queue()

        self.results = create_soft_signal_r(list[XrcResult], "results", self.name)
        self.x_position = create_soft_signal_r(float, "x_position", self.name)
        self.y_position = create_soft_signal_r(float, "y_position", self.name)
        self.z_position = create_soft_signal_r(float, "z_position", self.name)
        self.bbox_size_x = create_soft_signal_r(float, "bbox_size_x", self.name)
        self.bbox_size_y = create_soft_signal_r(float, "bbox_size_y", self.name)
        self.bbox_size_z = create_soft_signal_r(float, "bbox_size_z", self.name)
        self.results_valid = create_soft_signal_r(bool, "results_valid", self.name)
        self.set_readable_signals(
            read=[
                self.results,
                self.x_position,
                self.y_position,
                self.z_position,
                self.bbox_size_x,
                self.bbox_size_y,
                self.bbox_size_z,
                self.results_valid,
            ]
        )
        super().__init__(name)

    async def _put_results(self, results: Sequence[XrcResult]):
        await self.results._backend.put(list(results))
        results_recieved = len(results) > 0
        await self.results_valid._backend.put(results_recieved)
        c_o_m = results[0]["centre_of_mass"] if results_recieved else [0, 0, 0]
        bbox = bbox_size(results[0]) if results_recieved else [0, 0, 0]
        await self.x_position._backend.put(c_o_m[0])
        await self.y_position._backend.put(c_o_m[1])
        await self.z_position._backend.put(c_o_m[2])
        await self.bbox_size_x._backend.put(bbox[0])
        await self.bbox_size_y._backend.put(bbox[1])
        await self.bbox_size_z._backend.put(bbox[2])

    def kickoff(self) -> Status:
        """Subscribes to Zocalo rabbitmq queue and starts a timeout counter for results,
        by default 180 s. The returned status represents only that the subscription was
        successfully processed, not that processing results have been recieved."""

        status = Status(obj=self.kickoff)
        self._kickoff_run = True
        try:
            self._subscribe_to_results()
            status.set_finished()
        except Exception as e:
            status.set_exception(e)
        return status

    @AsyncStatus.wrap
    async def complete(self):
        """Returns an AsyncStatus waiting for results to be received from Zocalo."""

        assert self._kickoff_run, f"{self} kickoff was never run!"
        try:
            raw_results = await asyncio.wait_for(
                self._raw_results_received.get(), self.timeout_s
            )
            LOGGER.info(f"Zocalo: found {len(raw_results)} crystals.")
            # Sort from strongest to weakest in case of multiple crystals
            await self._put_results(
                sorted(raw_results, key=lambda d: d[self.sort_key], reverse=True)
            )
        finally:
            self._kickoff_run = False

    async def describe(self) -> dict[str, Descriptor]:
        return OrderedDict(
            [
                (
                    self._name + "-results",
                    {
                        "source": f"sim://{self._prefix}",
                        "dtype": "array",
                        "shape": [
                            -1,
                        ],  # TODO describe properly - see https://github.com/bluesky/event-model/issues/214
                    },
                ),
                (
                    self._name + "-x_position",
                    {
                        "source": f"sim://{self._prefix}",
                        "dtype": "number",
                        "shape": [],
                    },
                ),
                (
                    self._name + "-y_position",
                    {
                        "source": f"sim://{self._prefix}",
                        "dtype": "number",
                        "shape": [],
                    },
                ),
                (
                    self._name + "-z_position",
                    {
                        "source": f"sim://{self._prefix}",
                        "dtype": "number",
                        "shape": [],
                    },
                ),
                (
                    self._name + "-bbox_size_x",
                    {
                        "source": f"sim://{self._prefix}",
                        "dtype": "number",
                        "shape": [],
                    },
                ),
                (
                    self._name + "-bbox_size_y",
                    {
                        "source": f"sim://{self._prefix}",
                        "dtype": "number",
                        "shape": [],
                    },
                ),
                (
                    self._name + "-bbox_size_z",
                    {
                        "source": f"sim://{self._prefix}",
                        "dtype": "number",
                        "shape": [],
                    },
                ),
                (
                    self._name + "-results_valid",
                    {
                        "source": f"sim://{self._prefix}",
                        "dtype": "boolean",
                        "shape": [],
                    },
                ),
            ],
        )

    def _get_zocalo_connection(self):
        zc = zocalo.configuration.from_file()
        zc.activate_environment(self.zocalo_environment)

        transport = lookup("PikaTransport")()
        transport.connect()
        return transport

    def _subscribe_to_results(self):
        transport = self._get_zocalo_connection()

        def _receive_result(
            rw: workflows.recipe.RecipeWrapper, header: dict, message: dict
        ) -> None:
            LOGGER.info(f"Received {message}")
            recipe_parameters = rw.recipe_step["parameters"]  # type: ignore # this rw is initialised with a message so recipe step is not None
            LOGGER.info(f"Recipe step parameters: {recipe_parameters}")
            transport.ack(header)

            results = message.get("results", [])
            call_in_bluesky_event_loop(self._raw_results_received.put(results))

        workflows.recipe.wrap_subscribe(
            transport,
            self.channel,
            _receive_result,
            acknowledgement=True,
            allow_non_recipe_messages=False,
        )


ZOCALO_READING_PLAN_NAME = "zocalo reading"


def trigger_zocalo(zocalo: ZocaloResults):
    """A minimal utility plan which will wait for analysis results to be returned from
    Zocalo, and bundle them in a reading."""

    yield from bps.create(ZOCALO_READING_PLAN_NAME)
    yield from bps.kickoff(zocalo, wait=True)
    yield from bps.complete(zocalo, wait=True)
    yield from bps.read(zocalo)
    yield from bps.save()


def get_processing_results(
    zocalo: ZocaloResults,
) -> Generator[Any, Any, Union[Tuple[np.ndarray, np.ndarray], Tuple[None, None]]]:
    """A minimal plan which will extract an xray centring result and crystal bounding
    box size from the zocalo results."""
    results_recieved = yield from bps.rd(zocalo.results_valid)
    if results_recieved:
        return (
            np.array(
                [
                    (yield from bps.rd(zocalo.x_position)),
                    (yield from bps.rd(zocalo.y_position)),
                    (yield from bps.rd(zocalo.z_position)),
                ]
            )
            - np.array(
                [0.5, 0.5, 0.5]
            ),  # zocalo returns the centre of the grid box, but we want the corner
            np.array(
                [
                    (yield from bps.rd(zocalo.bbox_size_x)),
                    (yield from bps.rd(zocalo.bbox_size_y)),
                    (yield from bps.rd(zocalo.bbox_size_z)),
                ]
            ),
        )
    else:
        return (None, None)
