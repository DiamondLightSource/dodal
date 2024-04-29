from functools import partial
from unittest.mock import AsyncMock, MagicMock, patch

import bluesky.plan_stubs as bps
import numpy as np
import pytest
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core.async_status import AsyncStatus

from dodal.devices.zocalo.zocalo_results import (
    ZOCALO_READING_PLAN_NAME,
    NoZocaloSubscription,
    XrcResult,
    ZocaloResults,
    get_processing_result,
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

test_ispyb_ids = {"dcid": 0, "dcgid": 0}


@patch("dodal.devices.zocalo_results._get_zocalo_connection")
@pytest.fixture
async def mocked_zocalo_device(RE):
    async def device(results, run_setup=False):
        zd = ZocaloResults(zocalo_environment="test_env")

        @AsyncStatus.wrap
        async def mock_trigger(results):
            await zd._put_results(results, test_ispyb_ids)

        zd.trigger = MagicMock(side_effect=partial(mock_trigger, results))  # type: ignore
        await zd.connect()

        if run_setup:

            def plan():
                yield from bps.open_run()
                yield from bps.trigger_and_read([zd], name=ZOCALO_READING_PLAN_NAME)
                yield from bps.close_run()

            RE(plan())
        return zd

    return device


async def test_put_result_read_results(
    mocked_zocalo_device,
    RE,
) -> None:
    zocalo_device = await mocked_zocalo_device([], run_setup=True)
    await zocalo_device._put_results(TEST_RESULTS, test_ispyb_ids)
    reading = await zocalo_device.read()
    results: list[XrcResult] = reading["zocalo-results"]["value"]
    centres: list[XrcResult] = reading["zocalo-centres_of_mass"]["value"]
    bboxes: list[XrcResult] = reading["zocalo-bbox_sizes"]["value"]
    assert results == TEST_RESULTS
    assert np.all(centres == np.array([[1, 2, 3], [2, 3, 4], [4, 5, 6]]))
    assert np.all(bboxes[0] == [2, 2, 1])


async def test_rd_top_results(
    mocked_zocalo_device,
    RE,
):
    zocalo_device = await mocked_zocalo_device([], run_setup=True)
    await zocalo_device._put_results(TEST_RESULTS, test_ispyb_ids)

    def test_plan():
        bbox_size = yield from bps.rd(zocalo_device.bbox_sizes)
        assert len(bbox_size[0]) == 3  # type: ignore
        assert np.all(bbox_size[0] == np.array([2, 2, 1]))  # type: ignore
        centres_of_mass = yield from bps.rd(zocalo_device.centres_of_mass)
        assert len(centres_of_mass[0]) == 3  # type: ignore
        assert np.all(centres_of_mass[0] == np.array([1, 2, 3]))  # type: ignore

    RE(test_plan())


async def test_trigger_and_wait_puts_results(
    mocked_zocalo_device,
    RE,
):
    zocalo_device = await mocked_zocalo_device(TEST_RESULTS)
    zocalo_device._put_results = AsyncMock()
    zocalo_device._put_results.assert_not_called()

    def plan():
        yield from bps.open_run()
        yield from bps.trigger_and_read([zocalo_device], name=ZOCALO_READING_PLAN_NAME)
        yield from bps.close_run()

    RE(plan())
    zocalo_device._put_results.assert_called()


async def test_extraction_plan(mocked_zocalo_device, RE) -> None:
    zocalo_device: ZocaloResults = await mocked_zocalo_device(
        TEST_RESULTS, run_setup=False
    )

    def plan():
        yield from bps.open_run()
        yield from bps.trigger_and_read([zocalo_device], name=ZOCALO_READING_PLAN_NAME)
        com, bbox = yield from get_processing_result(zocalo_device)
        assert np.all(com == np.array([0.5, 1.5, 2.5]))
        assert np.all(bbox == np.array([2, 2, 1]))
        yield from bps.close_run()

    RE(plan())


@patch(
    "dodal.devices.zocalo.zocalo_results.workflows.recipe.wrap_subscribe", autospec=True
)
@patch("dodal.devices.zocalo.zocalo_results._get_zocalo_connection", autospec=True)
async def test_subscribe_only_on_called_stage(
    mock_connection: MagicMock, mock_wrap_subscribe: MagicMock, RE: RunEngine
):
    zocalo_results = ZocaloResults(
        name="zocalo", zocalo_environment="dev_artemis", timeout_s=2
    )
    mock_wrap_subscribe.assert_not_called()
    await zocalo_results.stage()
    mock_wrap_subscribe.assert_called_once()
    zocalo_results._raw_results_received.put([])
    RE(bps.trigger(zocalo_results))
    mock_wrap_subscribe.assert_called_once()
    zocalo_results._raw_results_received.put([])
    RE(bps.trigger(zocalo_results))
    zocalo_results._raw_results_received.put([])
    RE(bps.trigger(zocalo_results))
    mock_wrap_subscribe.assert_called_once()


@patch("dodal.devices.zocalo.zocalo_results._get_zocalo_connection", autospec=True)
async def test_when_exception_caused_by_zocalo_message_then_exception_propagated(
    mock_connection, RE: RunEngine
):
    zocalo_results = ZocaloResults(
        name="zocalo", zocalo_environment="dev_artemis", timeout_s=0.1
    )
    await zocalo_results.connect()
    with pytest.raises(FailedStatus) as e:
        RE(bps.trigger(zocalo_results, wait=True))

    assert isinstance(e.value.__cause__, NoZocaloSubscription)
