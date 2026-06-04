import time

import pytest
from ophyd_async.core import get_mock_put, init_devices
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.beamlines.i09.scaler import ScalerController


@pytest.fixture
def scaler1() -> ScalerController:
    with init_devices(mock=True):
        scaler1 = ScalerController("TEST:")
    return scaler1


async def test_scaler_controller_read(
    scaler1: ScalerController,
) -> None:
    await assert_reading(
        scaler1,
        {
            "scaler1-hm3amp20": partial_reading(0),
            "scaler1-sm5amp8": partial_reading(0),
            "scaler1-smpmamp39": partial_reading(0),
            "scaler1-rfdamp10": partial_reading(0),
        },
    )


async def test_scaler_controller_read_configuration(scaler1: ScalerController) -> None:
    await assert_configuration(scaler1, {"scaler1-count_time": partial_reading(0.0)})


async def test_scaler_controller_set(scaler1: ScalerController) -> None:
    value = 1
    await scaler1.set(value)
    get_mock_put(scaler1.count_time).assert_awaited_once_with(value)


async def test_scaler_controller_trigger_waits_for_counting_to_finish(
    scaler1: ScalerController,
) -> None:
    start = time.monotonic()
    await scaler1.trigger()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.01
    assert await scaler1.counting.get_value() is False


async def test_scaler_controller_trigger_sets_counting_true_then_false(
    scaler1: ScalerController,
) -> None:
    values = []
    scaler1.counting.subscribe(values.append)
    await scaler1.trigger()
    scaler1.counting.clear_sub(values.append)

    states = []
    expected_states = [False, True, False]
    for v in values:
        states.append(v[scaler1.counting.name]["value"])
    assert states == expected_states


async def test_scaler_controller_multiple_connects_has_one_subscribe(
    scaler1: ScalerController,
) -> None:
    expected_subscribers = 1
    number_of_subscribers = len(scaler1.counting._get_cache()._listeners)
    assert number_of_subscribers == expected_subscribers
    # Test if we connect again if another subscriber is added, checking for memory leaks.
    for _ in range(3):
        await scaler1.connect(mock=True)
        assert len(scaler1.counting._get_cache()._listeners) == expected_subscribers
