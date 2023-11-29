from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from dodal.devices.zocalo import NULL_RESULT, XrcResult, ZocaloInteractor, ZocaloResults

TEST_RESULT_LARGE: XrcResult = {
    "centre_of_mass": [1, 2, 3],
    "max_voxel": [1, 2, 3],
    "max_count": 105062,
    "n_voxels": 35,
    "total_count": 2387574,
    "bounding_box": [[2, 2, 2], [8, 8, 7]],
}


@pytest_asyncio.fixture
async def zocalo_device():
    zd = ZocaloResults("dev_artemis")
    await zd.connect()
    return zd


@pytest.mark.s03
@pytest.mark.asyncio
async def test_read_results_from_fake_zocalo(zocalo_device: ZocaloResults):
    zc = ZocaloInteractor("dev_artemis")
    zc.run_start(0)
    zc.run_end(0)
    await zocalo_device.trigger()
    results = await zocalo_device.read()
    assert results["zocalo_results-results"]["value"][0] == TEST_RESULT_LARGE
