from collections.abc import Mapping
from unittest import mock
from unittest.mock import AsyncMock, Mock

import pytest
from bluesky.plan_stubs import abs_set, prepare
from bluesky.plans import count
from bluesky.run_engine import RunEngine
from ophyd_async.core import callback_on_mock_put, init_devices, set_mock_value

from dodal.devices.current_amplifiers import (
    SR570,
    SR570_GAIN_CONFIGURATION,
    CountState,
    CurrentAmpDet,
    SR570FineGainTable,
    SR570GainTable,
    StruckScaler,
)


def sr570_setting_for_gain(
    gain: float,
) -> tuple[SR570GainTable, SR570FineGainTable]:
    """Find the coarse and fine settings for a sensitivity."""
    return next(
        (coarse, fine)
        for coarse, fine_gains in SR570_GAIN_CONFIGURATION.items()
        for fine, sensitivity in fine_gains.items()
        if sensitivity == gain
    )


@pytest.fixture
async def mock_sr570(prefix: str = "BLXX-EA-DET-007:", suffix: str = "Gain") -> SR570:
    async with init_devices(mock=True):
        mock_sr570 = SR570(
            prefix,
            suffix=suffix,
            fine_gain_table=SR570FineGainTable,
            coarse_gain_table=SR570GainTable,
            upperlimit=4.7,
            lowerlimit=0.4,
        )
    return mock_sr570


@pytest.fixture
async def mock_struck_scaler(
    prefix: str = "BLXX-EA-DET-007:", suffix: str = ".s17"
) -> StruckScaler:
    async with init_devices(mock=True):
        mock_struck_scaler = StruckScaler(
            prefix=prefix,
            suffix=suffix,
        )
    return mock_struck_scaler


@pytest.fixture
async def mock_sr570_struck_scaler_detector(
    mock_struck_scaler: StruckScaler,
    mock_sr570: SR570,
) -> CurrentAmpDet:
    async with init_devices(mock=True):
        mock_sr570_struck_scaler_detector = CurrentAmpDet(
            current_amp=mock_sr570,
            counter=mock_struck_scaler,
        )
    return mock_sr570_struck_scaler_detector


@pytest.mark.parametrize(
    "gain, wait_time",
    [(1e3, 1e-4), (1e6, 1e-4), (2e6, 0.15), (2e7, 0.15), (2e9, 0.2), (1e12, 0.2)],
)
@mock.patch("asyncio.sleep")
async def test_sr570_set(
    sleep: AsyncMock,
    mock_sr570: SR570,
    run_engine: RunEngine,
    gain: float,
    wait_time: float,
):
    run_engine(abs_set(mock_sr570, gain, wait=True))

    assert await mock_sr570.gain.get_value() == pytest.approx(gain)
    assert await mock_sr570.gain.get_value() == pytest.approx(gain)

    # Extra sleeps either side of set are Bluesky's sleep, which are set to 0.
    for actual, expected in zip(
        sleep.call_args[0], [0, 0, wait_time, 0, 0], strict=False
    ):
        assert actual == expected


@pytest.mark.parametrize("gain", [1e-2, 1, "ssdfsden_212341"])
@mock.patch("asyncio.sleep")
async def test_sr570_set_fail_out_of_range(
    sleep: AsyncMock,
    mock_sr570: SR570,
    gain,
):
    with pytest.raises(ValueError) as e:
        await mock_sr570.set(gain)

    available = [
        f"{sensitivity:.0e}"
        for fine_gains in SR570_GAIN_CONFIGURATION.values()
        for sensitivity in fine_gains.values()
    ]

    assert str(e.value) == (
        f"Gain value {gain} is not within {mock_sr570.name} range.\n"
        f"Available gains: {available}"
    )

    sleep.assert_not_called()


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        (1e3, 1, 1e4),
        (5e3, 5, 5e8),
        (2e4, 3, 2e7),
        (1e5, 6, 1e11),
    ],
)
@mock.patch("asyncio.sleep")
async def test_sr570_increase_gain(
    sleep: AsyncMock,
    mock_sr570: SR570,
    starting_gain: float,
    gain_change_count: int,
    final_gain: float,
):
    await mock_sr570.set(starting_gain)

    for _ in range(gain_change_count):
        await mock_sr570.increase_gain()

    assert await mock_sr570.gain.get_value() == pytest.approx(final_gain)
    assert sleep.call_count == gain_change_count + 1


@mock.patch("asyncio.sleep")
async def test_sr570_increase_gain_top_out_fail(
    sleep: AsyncMock,
    mock_sr570: SR570,
):
    max_gain = 1e12
    await mock_sr570.set(max_gain)

    with pytest.raises(ValueError):
        await mock_sr570.increase_gain()

    assert await mock_sr570.gain.get_value() == pytest.approx(max_gain)
    assert sleep.call_count == 2


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        (1e8, 5, 1e3),
        (5e9, 3, 5e6),
        (2e11, 3, 2e8),
        (1e12, 8, 1e4),
    ],
)
@mock.patch("asyncio.sleep")
async def test_sr570_decrease_gain(
    sleep: AsyncMock,
    mock_sr570: SR570,
    starting_gain: float,
    gain_change_count: int,
    final_gain: float,
):
    await mock_sr570.set(starting_gain)

    for _ in range(gain_change_count):
        await mock_sr570.decrease_gain()

    assert await mock_sr570.gain.get_value() == pytest.approx(final_gain)
    assert sleep.call_count == gain_change_count + 1


@mock.patch("asyncio.sleep")
async def test_sr570_decrease_gain_bottom_out_fail(
    sleep: AsyncMock,
    mock_sr570: SR570,
):
    min_gain = 1e3

    await mock_sr570.set(min_gain)

    with pytest.raises(ValueError):
        await mock_sr570.decrease_gain()

    assert await mock_sr570.gain.get_value() == pytest.approx(min_gain)
    assert sleep.call_count == 2


# class MockSR570RaiseTimeTable(float, Enum):
#     """Mock raise time(s) for SR570 current amplifier to speed up test."""

#     SEN_1 = 0
#     SEN_2 = 0
#     SEN_3 = 0
#     SEN_4 = 0


@pytest.mark.parametrize(
    "gain, raw_count, expected_current",
    [
        (1e3, 0.51e5, 0.51e-3),
        (5e3, -10e5, -2e-3),
        (2e6, 5.2e5, 2.6e-6),
        (2e8, 2.2e5, 1.1e-8),
        (2e10, 8.7e5, 4.35e-10),
        (2e4, 0.0, 0.0),
    ],
)
async def test_sr570_struck_scaler_read(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    mock_sr570_struck_scaler_detector,
    gain: float,
    raw_count: float,
    expected_current: float,
):
    coarse_gain, fine_gain = sr570_setting_for_gain(gain)

    current_amp = mock_sr570_struck_scaler_detector.current_amp()
    set_mock_value(current_amp.coarse_gain, coarse_gain)
    set_mock_value(current_amp.fine_gain, fine_gain)

    set_mock_value(mock_sr570_struck_scaler_detector.counter().readout, raw_count)
    set_mock_value(mock_sr570_struck_scaler_detector.counter().count_time, 1)
    set_mock_value(mock_sr570_struck_scaler_detector.auto_mode, False)

    run_engine(count([mock_sr570_struck_scaler_detector]))

    assert run_engine_documents["event"][0]["data"][
        "mock_sr570_struck_scaler_detector-current"
    ] == pytest.approx(expected_current)


@pytest.mark.parametrize(
    "gain, raw_count, expected_current",
    [
        (1e6, [1e2, 1e3, 1e4, 1e5, 1e5], 1e-9),
        (1e3, [1e5, 1e5], 1e-3),
        (1e6, [520e5, 52e5, 5.2e5, 5.2e4, 5.2e4], 5.2e-4),
        (1e9, [22.2e5, 2.22e5, 2.22e5], 2.22e-8),
        (2e4, [0.0] * (30 - 5), 0.0),
        (2e4, [-200.0e5, -20.0e5, -10.0e5, -10.0e5], -0.01),
        (1e11, [0.002e5, 0.004e5, 0.01e5, 0.02e5, 0.02e5], 2e-14),
    ],
)
async def test_sr570_struck_scaler_read_with_autogain(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    mock_sr570_struck_scaler_detector,
    gain: float,
    raw_count: list[float],
    expected_current: float,
):
    current_amp = mock_sr570_struck_scaler_detector.current_amp()
    await current_amp.set(gain)

    set_mock_value(mock_sr570_struck_scaler_detector.auto_mode, True)

    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = raw_count

    def set_mock_counter():
        set_mock_value(
            mock_sr570_struck_scaler_detector.counter().trigger_start, CountState.DONE
        )
        set_mock_value(
            mock_sr570_struck_scaler_detector.counter().readout, rbv_mocks.get()
        )

    callback_on_mock_put(
        mock_sr570_struck_scaler_detector.counter().trigger_start,
        lambda *_, **__: set_mock_counter(),
    )

    run_engine(prepare(mock_sr570_struck_scaler_detector, 1))
    run_engine(count([mock_sr570_struck_scaler_detector]))

    assert run_engine_documents["event"][0]["data"][
        "mock_sr570_struck_scaler_detector-current"
    ] == pytest.approx(expected_current, rel=1e-14)
