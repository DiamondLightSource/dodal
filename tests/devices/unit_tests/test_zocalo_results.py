from functools import partial
from typing import Awaitable, Callable, Sequence
from unittest.mock import MagicMock

import bluesky.plan_stubs as bps
import numpy as np
import pytest
import pytest_asyncio
from ophyd_async.core.async_status import AsyncStatus

from dodal.devices.zocalo import XrcResult, ZocaloResults, trigger_zocalo

TEST_RESULTS: list[XrcResult] = [
    {
        "centre_of_mass": [1, 2, 3],
        "max_voxel": [2, 4, 5],
        "max_count": 105062,
        "n_voxels": 38,
        "total_count": 2387574,
        "bounding_box": [[1, 2, 3], [3, 4, 4]],
    },
    {
        "centre_of_mass": [2, 3, 4],
        "max_voxel": [2, 4, 5],
        "max_count": 105123,
        "n_voxels": 35,
        "total_count": 2387574,
        "bounding_box": [[1, 2, 3], [3, 4, 4]],
    },
    {
        "centre_of_mass": [4, 5, 6],
        "max_voxel": [2, 4, 5],
        "max_count": 102062,
        "n_voxels": 31,
        "total_count": 2387574,
        "bounding_box": [[1, 2, 3], [3, 4, 4]],
    },
]

TEST_READING = {
    "zocalo_results-centre_of_mass": {
        "value": np.array([2, 3, 4]),
        "timestamp": 11250827.378482452,
        "alarm_severity": 0,
    },
    "zocalo_results-max_voxel": {
        "value": np.array([2, 4, 5]),
        "timestamp": 11250827.378502235,
        "alarm_severity": 0,
    },
    "zocalo_results-max_count": {
        "value": 105123,
        "timestamp": 11250827.378515247,
        "alarm_severity": 0,
    },
    "zocalo_results-n_voxels": {
        "value": 35,
        "timestamp": 11250827.37852733,
        "alarm_severity": 0,
    },
    "zocalo_results-total_count": {
        "value": 2387574,
        "timestamp": 11250827.378539408,
        "alarm_severity": 0,
    },
    "zocalo_results-bounding_box": {
        "value": np.array([[1, 2, 3], [3, 4, 4]]),
        "timestamp": 11250827.378558964,
        "alarm_severity": 0,
    },
}


@pytest_asyncio.fixture
async def mocked_zocalo_device(RE):
    async def device(results):
        zd = ZocaloResults(zocalo_environment="test_env")
        zd._get_zocalo_connection = MagicMock()

        @AsyncStatus.wrap
        async def mock_complete(results):
            await zd._put_results(results)

        zd.complete = MagicMock(side_effect=partial(mock_complete, results))  # type: ignore
        await zd.connect()

        def plan():
            yield from bps.open_run()
            yield from trigger_zocalo(zd)
            yield from bps.close_run()

        RE(plan())
        return zd

    return device


@pytest.mark.asyncio
async def test_put_result_read_results(
    mocked_zocalo_device: Callable[[Sequence[XrcResult]], Awaitable[ZocaloResults]], RE
):
    zocalo_device = await mocked_zocalo_device([])
    await zocalo_device._put_results(TEST_RESULTS)
    reading = await zocalo_device.read()
    results: list[XrcResult] = reading["zocalo_results-results"]["value"]
    centres: list[XrcResult] = reading["zocalo_results-centres_of_mass"]["value"]
    bboxes: list[XrcResult] = reading["zocalo_results-bbox_sizes"]["value"]
    assert results == TEST_RESULTS
    assert np.all(centres == np.array([[1, 2, 3], [2, 3, 4], [4, 5, 6]]))
    assert np.all(bboxes[0] == [2, 2, 1])


@pytest.mark.asyncio
async def test_rd_top_results(
    mocked_zocalo_device: Callable[[Sequence[XrcResult]], Awaitable[ZocaloResults]], RE
):
    zocalo_device = await mocked_zocalo_device([])
    await zocalo_device._put_results(TEST_RESULTS)

    def test_plan():
        bbox_size = yield from bps.rd(zocalo_device.bbox_sizes)
        assert len(bbox_size[0]) == 3
        assert np.all(bbox_size[0] == np.array([2, 2, 1]))
        centres_of_mass = yield from bps.rd(zocalo_device.centres_of_mass)
        assert len(centres_of_mass[0]) == 3
        assert np.all(centres_of_mass[0] == np.array([1, 2, 3]))

    RE(test_plan())
