import re
from collections.abc import Mapping
from unittest import mock
from unittest.mock import AsyncMock

import pytest
from bluesky.plan_stubs import abs_set
from bluesky.plans import count
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    callback_on_mock_put,
    get_mock_put,
    init_devices,
    set_mock_value,
)

from dodal.devices.current_amplifiers import (
    CountState,
    CurrentAmpDet,
    Femto3xxRaiseTime,
    FemtoDDPCA,
    StruckScaler,
)


@pytest.fixture
async def mock_femto(
    prefix: str = "BLXX-EA-DET-007:", suffix: str = "Gain"
) -> FemtoDDPCA:
    async with init_devices(mock=True):
        mock_femto = FemtoDDPCA(prefix=prefix, suffix=suffix)
    return mock_femto


@pytest.fixture
async def mock_struck_scaler(
    prefix: str = "BLXX-EA-DET-007:", suffix: str = ".s17"
) -> StruckScaler:
    async with init_devices(mock=True):
        mock_struck_scaler = StruckScaler(prefix=prefix, suffix=suffix)
    return mock_struck_scaler


@pytest.fixture
async def mock_femto_struck_scaler_detector(
    mock_struck_scaler: StruckScaler,
    mock_femto: FemtoDDPCA,
) -> CurrentAmpDet:
    async with init_devices(mock=True):
        mock_femto_struck_scaler_detector = CurrentAmpDet(
            current_amp=mock_femto, counter=mock_struck_scaler
        )
    return mock_femto_struck_scaler_detector


@pytest.mark.parametrize(
    "expected_gain, wait_time",
    [(1e4, 0.8e-3), (1e6, 0.8e-3), (1e8, 2.3e-3), (1e10, 17e-3), (1e13, 350e-3)],
)
@mock.patch("asyncio.sleep")
async def test_femto_set(
    sleep: AsyncMock,
    mock_femto: FemtoDDPCA,
    run_engine: RunEngine,
    expected_gain: float,
    wait_time: float,
):
    run_engine(abs_set(mock_femto, expected_gain, wait=True))

    assert await mock_femto.gain.get_value() == expected_gain

    # Extra sleeps either side of set are bluesky's sleep, which are set to 0.
    for actual, expected in zip(
        sleep.call_args[0], [0, 0, wait_time, 0, 0], strict=False
    ):
        assert actual == expected


@pytest.mark.parametrize("gain", [1e3, 1e14, -1.0, 0.0])
@mock.patch("asyncio.sleep")
async def test_femto_set_fail_out_of_range(
    sleep: AsyncMock,
    mock_femto: FemtoDDPCA,
    gain: float,
):
    with pytest.raises(
        ValueError,
        match=re.escape(
            f"Gain value {gain} is not within "
            f"{mock_femto.name} range."
            f"\nAvailable gains: "
            "['1e+04', '1e+05', '1e+06', '1e+07', '1e+08', '1e+09', '1e+10', '1e+11', '1e+12', '1e+13']"
        ),
    ):
        await mock_femto.set(gain)

    get_mock_put(mock_femto.gain_setting).assert_not_called()
    sleep.assert_not_called()


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        (1e4, 1, 1e5),
        (1e6, 2, 1e8),
        (1e8, 3, 1e11),
    ],
)
@mock.patch("asyncio.sleep")
async def test_femto_increase_gain(
    sleep: AsyncMock,
    mock_femto: FemtoDDPCA,
    starting_gain: float,
    gain_change_count: int,
    final_gain: float,
):
    await mock_femto.set(starting_gain)
    sleep.reset_mock()

    for _ in range(gain_change_count):
        await mock_femto.increase_gain()

    assert await mock_femto.gain.get_value() == final_gain

    # Each increase should wait for the settling time of the resulting gain.
    assert sleep.await_count == gain_change_count


@mock.patch("asyncio.sleep")
async def test_femto_increase_gain_fail_at_max_gain(
    sleep: AsyncMock,
    mock_femto: FemtoDDPCA,
):
    max_gain = 1e13
    await mock_femto.set(max_gain)

    with pytest.raises(ValueError, match=re.escape("Gain at max value of 1e+13.")):
        await mock_femto.increase_gain()

    assert await mock_femto.gain.get_value() == max_gain

    sleep.assert_any_await(Femto3xxRaiseTime.SEN_10.value)


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        (1e9, 2, 1e7),
        (1e11, 3, 1e8),
        (1e13, 9, 1e4),
    ],
)
@mock.patch("asyncio.sleep")
async def test_femto_decrease_gain(
    sleep: AsyncMock,
    mock_femto: FemtoDDPCA,
    starting_gain: float,
    gain_change_count: int,
    final_gain: float,
):
    await mock_femto.set(starting_gain)
    sleep.reset_mock()

    for _ in range(gain_change_count):
        await mock_femto.decrease_gain()

    assert await mock_femto.gain.get_value() == final_gain

    # Each decrease should wait for the settling time of the resulting gain.
    assert sleep.await_count == gain_change_count


@mock.patch("asyncio.sleep")
async def test_femto_decrease_gain_fail_at_min_gain(
    sleep: AsyncMock,
    mock_femto: FemtoDDPCA,
):
    min_gain = 1e4
    await mock_femto.set(min_gain)

    with pytest.raises(ValueError, match=re.escape("Gain at min value of 1e+04")):
        await mock_femto.decrease_gain()

    assert await mock_femto.gain.get_value() == min_gain
    sleep.assert_any_await(Femto3xxRaiseTime.SEN_1.value)


@pytest.mark.parametrize(
    "gain, raw_voltage, expected_current",
    [
        (1e4, 0.51e5, 0.51e-4),
        (1e6, -10e5, -10e-6),
        (1e9, 5.2e5, 5.2e-9),
        (1e12, 2.2e5, 2.2e-12),
        (1e13, 8.7e5, 8.7e-13),
        (1e8, 0.0, 0.0),
    ],
)
async def test_femto_struck_scaler_read(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    mock_femto: FemtoDDPCA,
    mock_struck_scaler: StruckScaler,
    mock_femto_struck_scaler_detector: CurrentAmpDet,
    gain: float,
    raw_voltage: float,
    expected_current: float,
):
    await mock_femto.set(gain)

    set_mock_value(mock_struck_scaler.current_count_time, 1)
    set_mock_value(mock_struck_scaler.current_count, raw_voltage)
    set_mock_value(mock_femto_struck_scaler_detector.auto_mode, False)

    run_engine(count([mock_femto_struck_scaler_detector]))

    assert run_engine_documents["event"][0]["data"][
        "mock_femto_struck_scaler_detector-current"
    ] == pytest.approx(expected_current)


@pytest.mark.parametrize(
    "gain, raw_voltage, expected_current",
    [
        (1e13, [1e9, 1e8, 1e7, 1e6] + [1e5] * 2, 1e-9),
        (1e4, [4e2, 4e3, 4e4] + [4e5] * 2, 4e-7),
        (1e9, [520e5, 52e5, 5.2e5, 5.2e5], 5.2e-7),
        (1e12, [2.2e5, 2.2e5], 2.2e-12),
        (1e13, [0.17e5, 0.17e5], 0.17e-13),
        (1e8, [0.0] * 7, 0.0),
        (1e8, [-200.0e5, -20.0e5, -2.0e5, -2.0e5], -2e-6),
        (1e4, [10.0e-6] * 30, 1.0e-23),
    ],
)
async def test_femto_struck_scaler_read_with_auto_gain(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    mock_femto: FemtoDDPCA,
    mock_struck_scaler: StruckScaler,
    mock_femto_struck_scaler_detector: CurrentAmpDet,
    gain: float,
    raw_voltage: list[float],
    expected_current: float,
):
    await mock_femto.set(gain)

    set_mock_value(mock_struck_scaler.current_count_time, 1)
    set_mock_value(mock_femto_struck_scaler_detector.auto_mode, True)

    raw_counts = iter(raw_voltage)

    def set_mock_counter():
        set_mock_value(mock_struck_scaler.current_count, next(raw_counts))
        set_mock_value(mock_struck_scaler.trigger_start, CountState.DONE)

    callback_on_mock_put(
        mock_struck_scaler.trigger_start,
        lambda *_, **__: set_mock_counter(),
    )

    run_engine(count([mock_femto_struck_scaler_detector]))

    assert run_engine_documents["event"][0]["data"][
        "mock_femto_struck_scaler_detector-current"
    ] == pytest.approx(expected_current, rel=1e-14)
