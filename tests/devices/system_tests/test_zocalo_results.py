import asyncio
import os

import bluesky.plan_stubs as bps
import psutil
import pytest
from bluesky.preprocessors import stage_decorator
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus

import dodal.devices.zocalo.zocalo_results
from dodal.devices.zocalo import (
    NoZocaloSubscription,
    XrcResult,
    ZocaloResults,
    ZocaloStartInfo,
    ZocaloTrigger,
)

TEST_RESULT_LARGE: XrcResult = {
    "centre_of_mass": [1, 2, 3],
    "max_voxel": [1, 2, 3],
    "max_count": 105062,
    "n_voxels": 35,
    "total_count": 2387574,
    "bounding_box": [[2, 2, 2], [8, 8, 7]],
}


@pytest.fixture
async def zocalo_device():
    zd = ZocaloResults()
    await zd.connect()
    return zd


@pytest.mark.s03
async def test_read_results_from_fake_zocalo(
    zocalo_device: ZocaloResults, RE: RunEngine
):
    zocalo_device._subscribe_to_results()
    zc = ZocaloTrigger("dev_artemis")
    zc.run_start(ZocaloStartInfo(0, None, 0, 100, 0))
    zc.run_end(0)
    zocalo_device.timeout_s = 5

    def plan():
        yield from bps.open_run()
        yield from bps.trigger_and_read([zocalo_device])
        yield from bps.close_run()

    RE(plan())

    results = await zocalo_device.read()
    assert results["zocalo-results"]["value"][0] == TEST_RESULT_LARGE


@pytest.mark.s03
async def test_stage_unstage_controls_read_results_from_fake_zocalo(
    zocalo_device: ZocaloResults, RE: RunEngine
):
    dodal.devices.zocalo.zocalo_results.CLEAR_QUEUE_WAIT_S = 0.05
    zc = ZocaloTrigger("dev_artemis")
    zocalo_device.timeout_s = 5

    def plan():
        yield from bps.open_run()
        zc.run_start(ZocaloStartInfo(0, None, 0, 100, 0))
        zc.run_end(0)
        yield from bps.sleep(0.15)
        yield from bps.trigger_and_read([zocalo_device])
        yield from bps.close_run()

    @stage_decorator([zocalo_device])
    def plan_with_stage():
        yield from plan()

    # With stage, the plan should run normally
    RE(plan_with_stage())
    # Without stage, the plan should run fail because we didn't connect to Zocalo
    with pytest.raises(FailedStatus) as e:
        RE(plan())
    assert isinstance(e.value.__cause__, NoZocaloSubscription)
    # And the results generated by triggering in plan() shouldn't make it to the zocalo device
    assert zocalo_device._raw_results_received.empty()

    # But we triggered it, so the results should be in the RMQ queue
    zocalo_device._subscribe_to_results()
    await asyncio.sleep(1)

    results = await zocalo_device.read()
    assert results["zocalo-results"]["value"][0] == TEST_RESULT_LARGE
    await zocalo_device.unstage()

    # Generating some more results leaves them at RMQ
    with pytest.raises(FailedStatus) as e:
        RE(plan())
    # But waiting for stage should clear them
    RE(bps.stage(zocalo_device, wait=True))
    assert zocalo_device._raw_results_received.empty()


@pytest.mark.s03
async def test_stale_connections_closed_after_unstage(
    zocalo_device: ZocaloResults, RE: RunEngine
):
    this_process = psutil.Process(os.getpid())

    connections_before = len(this_process.connections())

    def stage_unstage():
        yield from bps.stage(zocalo_device)
        yield from bps.unstage(zocalo_device)

    RE(stage_unstage())

    connections_after = len(this_process.connections())

    assert connections_before == connections_after
