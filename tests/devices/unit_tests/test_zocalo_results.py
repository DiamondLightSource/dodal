from collections import deque
from typing import Awaitable, Callable, Sequence
from unittest.mock import MagicMock

import numpy as np
import pytest
import pytest_asyncio

from dodal.devices.zocalo import (
    XrcResult,
    ZocaloResults,
)

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
async def mocked_zocalo_device():
    async def device(results):
        zd = ZocaloResults("test_env")
        zd._wait_for_results = MagicMock(return_value=results)
        await zd.connect()
        return zd

    return device


@pytest.mark.asyncio
async def test_put_result(
    mocked_zocalo_device: Callable[[Sequence[XrcResult]], Awaitable[ZocaloResults]]
):
    zocalo_device = await mocked_zocalo_device([])
    await zocalo_device._put_results(TEST_RESULTS)


@pytest.mark.asyncio
async def test_read_gets_results(
    mocked_zocalo_device: Callable[[Sequence[XrcResult]], Awaitable[ZocaloResults]],
):
    zocalo_device = await mocked_zocalo_device(TEST_RESULTS)
    results = await zocalo_device.read()
    data: deque[XrcResult] = results["zocalo_results-results"]["value"]

    assert data[0] == TEST_RESULTS[0]
    assert data[1] == TEST_RESULTS[1]
    assert data[2] == TEST_RESULTS[2]


@pytest.mark.asyncio
async def test_failed_read_gets_empty_deque(
    mocked_zocalo_device: Callable[[Sequence[XrcResult]], Awaitable[ZocaloResults]],
):
    zocalo_device = await mocked_zocalo_device([])
    results = await zocalo_device.read()
    data: deque[XrcResult] = results["zocalo_results-results"]["value"]
    assert len(data) == 0
    assert isinstance(data, deque)
