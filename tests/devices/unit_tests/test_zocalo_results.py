from unittest.mock import AsyncMock, MagicMock, patch

import bluesky.plan_stubs as bps
import numpy as np
import pytest
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus

from dodal.devices.zocalo.zocalo_results import (
    ZOCALO_READING_PLAN_NAME,
    NoZocaloSubscription,
    XrcResult,
    ZocaloResults,
    get_processing_result,
)
from dodal.testing_utils import constants


async def test_put_result_read_results(get_mock_zocalo_device, RE) -> None:
    zocalo_device = await get_mock_zocalo_device([], run_setup=True)
    await zocalo_device._put_results(constants.ZOC_RESULTS, constants.ZOC_ISPYB_IDS)
    reading = await zocalo_device.read()
    results: list[XrcResult] = reading["zocalo-results"]["value"]
    centres: list[XrcResult] = reading["zocalo-centres_of_mass"]["value"]
    bboxes: list[XrcResult] = reading["zocalo-bbox_sizes"]["value"]
    assert results == constants.ZOC_RESULTS
    assert np.all(centres == np.array([[1, 2, 3], [2, 3, 4], [4, 5, 6]]))
    assert np.all(bboxes[0] == [2, 2, 1])


async def test_rd_top_results(get_mock_zocalo_device, RE):
    zocalo_device = await get_mock_zocalo_device([], run_setup=True)
    await zocalo_device._put_results(constants.ZOC_RESULTS, constants.ZOC_ISPYB_IDS)

    def test_plan():
        bbox_size = yield from bps.rd(zocalo_device.bbox_sizes)
        assert len(bbox_size[0]) == 3  # type: ignore
        assert np.all(bbox_size[0] == np.array([2, 2, 1]))  # type: ignore
        centres_of_mass = yield from bps.rd(zocalo_device.centres_of_mass)
        assert len(centres_of_mass[0]) == 3  # type: ignore
        assert np.all(centres_of_mass[0] == np.array([1, 2, 3]))  # type: ignore

    RE(test_plan())


async def test_trigger_and_wait_puts_results(get_mock_zocalo_device, RE):
    zocalo_device = await get_mock_zocalo_device(constants.ZOC_RESULTS)
    zocalo_device._put_results = AsyncMock()
    zocalo_device._put_results.assert_not_called()

    def plan():
        yield from bps.open_run()
        yield from bps.trigger_and_read([zocalo_device], name=ZOCALO_READING_PLAN_NAME)
        yield from bps.close_run()

    RE(plan())
    zocalo_device._put_results.assert_called()


async def test_extraction_plan(get_mock_zocalo_device, RE) -> None:
    zocalo_device: ZocaloResults = await get_mock_zocalo_device(
        constants.ZOC_RESULTS, run_setup=False
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
