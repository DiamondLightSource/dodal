from functools import partial
from queue import Empty
from unittest.mock import AsyncMock, MagicMock, call, patch

import bluesky.plan_stubs as bps
import numpy as np
import pytest
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import AsyncStatus

from dodal.devices.zocalo.zocalo_constants import ZOCALO_ENV
from dodal.devices.zocalo.zocalo_results import (
    NoResultsFromZocalo,
    NoZocaloSubscription,
    XrcResult,
    ZocaloResults,
    ZocaloSource,
    get_full_processing_results,
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
    {
        "centre_of_mass": [0.5, 1, 2],
        "max_voxel": [0, 1, 2],
        "max_count": 1500,
        "n_voxels": 3,
        "total_count": 1800,
        "bounding_box": [[0, 1, 1], [1, 2, 4]],
    },
    {
        "centre_of_mass": [2.2, 3.5, 4.7],
        "max_voxel": [3, 4, 4],
        "max_count": 150000,
        "n_voxels": 14,
        "total_count": 1800000,
        "bounding_box": [[2, 2, 3], [4, 5, 6]],
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

test_recipe_parameters = {"dcid": 0, "dcgid": 0}


@pytest.fixture
async def zocalo_results():
    with (
        patch("dodal.devices.zocalo.zocalo_results._get_zocalo_connection"),
        patch("dodal.devices.zocalo.zocalo_results.CLEAR_QUEUE_WAIT_S", 0),
    ):
        yield ZocaloResults(name="zocalo", zocalo_environment=ZOCALO_ENV)


@pytest.fixture
async def mocked_zocalo_device(RE: RunEngine, zocalo_results: ZocaloResults):
    async def device(results):
        @AsyncStatus.wrap
        async def mock_trigger(results):
            await zocalo_results._put_results(results, test_recipe_parameters)

        zocalo_results.trigger = MagicMock(side_effect=partial(mock_trigger, results))  # type: ignore
        await zocalo_results.connect()
        return zocalo_results

    return device


async def test_trigger_and_wait_puts_results(
    mocked_zocalo_device,
    RE,
):
    zocalo_device = await mocked_zocalo_device(TEST_RESULTS)
    zocalo_device._put_results = AsyncMock()
    zocalo_device._put_results.assert_not_called()

    RE(bps.trigger(zocalo_device))
    zocalo_device._put_results.assert_called()


async def test_get_full_processing_results(mocked_zocalo_device, RE) -> None:
    zocalo_device: ZocaloResults = await mocked_zocalo_device(TEST_RESULTS)

    def plan():
        yield from bps.trigger(zocalo_device)
        full_results = yield from get_full_processing_results(zocalo_device)
        assert len(full_results) == len(TEST_RESULTS)
        centres_of_mass = [xrc_result["centre_of_mass"] for xrc_result in full_results]
        bbox = [xrc_result["bounding_box"] for xrc_result in full_results]
        assert np.all(
            np.isclose(
                centres_of_mass,
                [
                    [0.5, 1.5, 2.5],
                    [1.5, 2.5, 3.5],
                    [3.5, 4.5, 5.5],
                    [0.0, 0.5, 1.5],
                    [1.7, 3.0, 4.2],
                ],
            )
        )
        assert bbox == [
            [[1, 2, 3], [3, 4, 4]],
            [[1, 2, 3], [3, 4, 4]],
            [[1, 2, 3], [3, 4, 4]],
            [[0, 1, 1], [1, 2, 4]],
            [[2, 2, 3], [4, 5, 6]],
        ]
        for prop in ["max_voxel", "max_count", "n_voxels", "total_count"]:
            assert [r[prop] for r in full_results] == [r[prop] for r in TEST_RESULTS]  # type: ignore

    RE(plan())


@patch(
    "dodal.devices.zocalo.zocalo_results.workflows.recipe.wrap_subscribe", autospec=True
)
@patch("dodal.devices.zocalo.zocalo_results._get_zocalo_connection", autospec=True)
@patch("dodal.devices.zocalo.zocalo_results.CLEAR_QUEUE_WAIT_S", 0)
async def test_subscribe_only_on_called_stage(
    mock_connection: MagicMock, mock_wrap_subscribe: MagicMock, RE: RunEngine
):
    zocalo_results = ZocaloResults(
        name="zocalo", zocalo_environment=ZOCALO_ENV, timeout_s=0
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


@patch("dodal.devices.zocalo.zocalo_results.LOGGER")
@patch(
    "dodal.devices.zocalo.zocalo_results.workflows.recipe.wrap_subscribe", autospec=True
)
@patch("dodal.devices.zocalo.zocalo_results._get_zocalo_connection", new=MagicMock())
async def test_zocalo_results_trigger_log_message(
    mock_wrap_subscribe, mock_logger, RE: RunEngine
):
    zocalo_results = ZocaloResults(
        name="zocalo",
        zocalo_environment=ZOCALO_ENV,
        timeout_s=0,
        use_cpu_and_gpu=True,
    )

    recipe_wrapper = MagicMock()
    recipe_wrapper.recipe_step = {"parameters": {}}

    def zocalo_plan():
        yield from bps.stage(zocalo_results)
        receive_result = mock_wrap_subscribe.mock_calls[0].args[2]
        receive_result(
            recipe_wrapper,
            {},
            {
                "results": [TEST_RESULTS[0]],
                "status": "success",
                "type": "3d",
            },
        )
        yield from bps.trigger(zocalo_results)

    RE(zocalo_plan())
    mock_logger.info.assert_has_calls(
        [
            call(
                f"Zocalo results from {ZocaloSource.CPU.value} processing: found 1 crystals."
            )
        ]
    )


@patch("dodal.devices.zocalo.zocalo_results._get_zocalo_connection", autospec=True)
async def test_when_exception_caused_by_zocalo_message_then_exception_propagated(
    mock_connection, RE: RunEngine
):
    zocalo_results = ZocaloResults(
        name="zocalo", zocalo_environment=ZOCALO_ENV, timeout_s=0.1
    )
    await zocalo_results.connect()
    with pytest.raises(FailedStatus) as e:
        RE(bps.trigger(zocalo_results, wait=True))

    assert isinstance(e.value.__cause__, NoZocaloSubscription)


async def test_if_use_cpu_and_gpu_zocalos_then_wait_twice_for_results(
    zocalo_results: ZocaloResults, RE: RunEngine
):
    zocalo_results.use_cpu_and_gpu = True
    await zocalo_results.stage()
    zocalo_results._raw_results_received.put([])
    zocalo_results._raw_results_received.put([])
    zocalo_results._raw_results_received.get = MagicMock()
    RE(bps.trigger(zocalo_results, wait=False))
    assert zocalo_results._raw_results_received.get.call_count == 2


async def test_if_use_gpu_then_only_use_first_result(
    zocalo_results: ZocaloResults, RE: RunEngine
):
    zocalo_results.use_gpu = True
    await zocalo_results.stage()
    zocalo_results._raw_results_received.put([])
    zocalo_results._raw_results_received.put([])
    zocalo_results._raw_results_received.get = MagicMock()
    RE(bps.trigger(zocalo_results, wait=False))
    assert zocalo_results._raw_results_received.get.call_count == 1


@patch("dodal.devices.zocalo.zocalo_results.LOGGER")
async def test_source_of_zocalo_results_correctly_identified(
    mock_logger, zocalo_results: ZocaloResults, RE: RunEngine
):
    zocalo_results.use_cpu_and_gpu = False
    await zocalo_results.stage()

    zocalo_results._raw_results_received.get = MagicMock(
        return_value={"recipe_parameters": {"test": 0}, "results": []}
    )
    RE(bps.trigger(zocalo_results, wait=False))
    mock_logger.info.assert_has_calls(
        [
            call(
                f"Zocalo results from {ZocaloSource.CPU.value} processing: found 0 crystals."
            )
        ]
    )


@patch("dodal.devices.zocalo.zocalo_results.LOGGER")
async def test_if_zocalo_results_timeout_from_gpu_then_warn(
    mock_logger, zocalo_results: ZocaloResults, RE: RunEngine
):
    zocalo_results.use_cpu_and_gpu = True
    await zocalo_results.stage()
    zocalo_results._raw_results_received.get = MagicMock(
        side_effect=[
            {"recipe_parameters": {"test": 0}, "results": []},
            Empty,
        ]
    )
    RE(bps.trigger(zocalo_results, wait=False))
    mock_logger.warning.assert_called_with(
        f"Zocalo results from GPU timed out. Using results from {ZocaloSource.CPU.value}"
    )


async def test_given_comparing_results_if_zocalo_results_from_gpu_but_not_cpu_then_error(
    zocalo_results: ZocaloResults, RE: RunEngine
):
    zocalo_results.use_cpu_and_gpu = True
    await zocalo_results.stage()
    zocalo_results._raw_results_received.get = MagicMock(
        side_effect=[
            {
                "recipe_parameters": {"test": 0, "gpu": True},
                "results": [TEST_RESULTS[0]],
            },
            Empty,
        ]
    )
    with pytest.raises(NoResultsFromZocalo):
        await zocalo_results.trigger()


async def test_given_using_gpu_results_if_zocalo_results_from_gpu_but_not_cpu_then_uses_gpu(
    zocalo_results: ZocaloResults, RE: RunEngine
):
    zocalo_results.use_gpu = True
    await zocalo_results.stage()
    zocalo_results._raw_results_received.get = MagicMock(
        side_effect=[
            {
                "recipe_parameters": {"dcgid": 0, "dcid": 0, "gpu": True},
                "results": [TEST_RESULTS[0]],
            },
            Empty,
        ]
    )
    await zocalo_results.trigger()
    assert len(await zocalo_results.centre_of_mass.get_value())


@patch("dodal.devices.zocalo.zocalo_results.LOGGER")
async def test_given_comparing_results_if_cpu_results_arrive_before_gpu_then_warn(
    mock_logger, zocalo_results: ZocaloResults, RE: RunEngine
):
    zocalo_results.use_cpu_and_gpu = True
    await zocalo_results.stage()
    zocalo_results._raw_results_received.get = MagicMock(
        return_value={"recipe_parameters": {"test": 0}, "results": []}
    )
    RE(bps.trigger(zocalo_results, wait=False))
    mock_logger.warning.assert_called_with(
        f"Received zocalo results from {ZocaloSource.CPU.value} before {ZocaloSource.GPU.value}"
    )


@pytest.mark.parametrize(
    "dict1,dict2,output",
    [
        (
            {"recipe_parameters": {"gpu": True}, "results": [{"test": 0}]},
            {"recipe_parameters": {}, "results": [{"test": 1}]},
            "Zocalo results from GPU and CPU are not identical.\n Results from GPU: {'test': 0}\n Results from CPU: {'test': 1}",
        ),
        (
            {
                "recipe_parameters": {"gpu": True},
                "results": [{"test": [[1, 2 + 1e-6, 3], [1, 2, 3]]}],
            },
            {"recipe_parameters": {}, "results": [{"test": [[1, 2, 3], [1, 2, 3]]}]},
            None,
        ),
        (
            {
                "recipe_parameters": {"gpu": True},
                "results": [
                    {"test": [[1, 2 + 1e-6, 3], [1, 2, 3]], "extra_key": "test"}
                ],
            },
            {"recipe_parameters": {}, "results": [{"test": [[1, 2, 3], [1, 2, 3]]}]},
            "Zocalo results from GPU and CPU are not identical.\n Results from GPU: {'test': [[1, 2.000001, 3], [1, 2, 3]], 'extra_key': 'test'}\n Results from CPU: {'test': [[1, 2, 3], [1, 2, 3]]}",
        ),
        (
            {
                "recipe_parameters": {"gpu": False},
                "results": [{"test": [[1, 2 + 1e-6, 3], [1, 2, 3]]}],
            },
            {"recipe_parameters": {}, "results": [{"test": [[1, 3, 3], [1, 2, 3]]}]},
            "Zocalo results from CPU and CPU are not identical.\n Results from CPU: {'test': [[1, 2.000001, 3], [1, 2, 3]]}\n Results from CPU: {'test': [[1, 3, 3], [1, 2, 3]]}",
        ),
    ],
)
@patch("dodal.devices.zocalo.zocalo_results.LOGGER")
async def test_given_comparing_results_then_warning_if_results_are_different(
    mock_logger, zocalo_results: ZocaloResults, RE: RunEngine, dict1, dict2, output
):
    zocalo_results.use_cpu_and_gpu = True

    await zocalo_results.stage()
    zocalo_results._raw_results_received.get = MagicMock(
        side_effect=[
            dict1,
            dict2,
        ]
    )
    RE(bps.trigger(zocalo_results, wait=False))
    mock_logger.warning.assert_called_with(
        output
    ) if output else mock_logger.warning.assert_not_called()


async def test_if_zocalo_results_timeout_before_any_results_then_error(
    zocalo_results: ZocaloResults,
):
    zocalo_results.use_cpu_and_gpu = True
    await zocalo_results.stage()
    zocalo_results._raw_results_received.get = MagicMock(side_effect=Empty)
    with pytest.raises(NoResultsFromZocalo):
        await zocalo_results.trigger()


@pytest.mark.parametrize(
    "gpu,",
    [(True), (False)],
)
@patch("dodal.devices.zocalo.zocalo_results.LOGGER")
@patch(
    "dodal.devices.zocalo.zocalo_results.workflows.recipe.wrap_subscribe", autospec=True
)
@patch("dodal.devices.zocalo.zocalo_results._get_zocalo_connection", new=MagicMock())
@patch("dodal.devices.zocalo.zocalo_results.CLEAR_QUEUE_WAIT_S", 0.1)
async def test_gpu_results_ignored_and_cpu_results_used_if_toggle_disabled(
    mock_wrap_subscribe, mock_logger, RE: RunEngine, gpu: bool
):
    zocalo_results = ZocaloResults(
        name="zocalo",
        zocalo_environment=ZOCALO_ENV,
        timeout_s=0,
        use_cpu_and_gpu=False,
    )

    recipe_wrapper = MagicMock()
    recipe_wrapper.recipe_step = {"parameters": {"gpu": gpu}}

    def zocalo_plan():
        yield from bps.stage(zocalo_results)
        receive_result = mock_wrap_subscribe.mock_calls[0].args[2]
        receive_result(
            recipe_wrapper,
            {},
            {
                "results": [TEST_RESULTS[0]],
                "status": "success",
                "type": "3d",
            },
        )
        yield from bps.trigger(zocalo_results)
        if gpu:
            mock_logger.warning.assert_called_with(
                "Timed out waiting for zocalo results!"
            )
        else:
            mock_logger.info.assert_called_with(
                f"Zocalo results from {ZocaloSource.CPU.value} processing: found 1 crystals."
            )

    RE(zocalo_plan())


async def test_given_comparing_results_when_no_results_found_then_returns_no_results(
    zocalo_results: ZocaloResults,
):
    zocalo_results.use_cpu_and_gpu = True
    await zocalo_results.stage()
    zocalo_results._raw_results_received.get = MagicMock(
        side_effect=[
            {"recipe_parameters": {"dcgid": 0, "dcid": 0, "gpu": True}, "results": []},
            {"recipe_parameters": {"dcgid": 0, "dcid": 0}, "results": []},
        ]
    )
    await zocalo_results.trigger()
    assert len(await zocalo_results.centre_of_mass.get_value()) == 0


@patch("dodal.devices.zocalo.zocalo_results.LOGGER")
async def test_given_using_gpu_results_if_results_from_cpu_first_then_warn_and_use(
    mock_logger: MagicMock, zocalo_results: ZocaloResults
):
    zocalo_results.use_gpu = True
    await zocalo_results.stage()
    zocalo_results._raw_results_received.get = MagicMock(
        side_effect=[
            {
                "recipe_parameters": {"dcgid": 0, "dcid": 0},
                "results": [TEST_RESULTS[0]],
            },
        ]
    )
    await zocalo_results.trigger()
    assert len(await zocalo_results.centre_of_mass.get_value())
    mock_logger.warning.assert_called_with(
        "Configured to use GPU results but CPU came first, using CPU results."
    )


async def test_given_using_gpu_results_and_comparing_results_both_on_then_error_when_staged(
    zocalo_results: ZocaloResults,
):
    zocalo_results.use_gpu = True
    zocalo_results.use_cpu_and_gpu = True
    with pytest.raises(ValueError):
        await zocalo_results.stage()
