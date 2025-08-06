from collections import defaultdict
from enum import Enum
from unittest import mock
from unittest.mock import AsyncMock, Mock

import pytest
from bluesky.plan_stubs import abs_set, prepare
from bluesky.plans import count
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    init_devices,
)
from ophyd_async.testing import callback_on_mock_put, set_mock_value

from dodal.devices.current_amplifiers import (
    SR570,
    SR570FineGainTable,
    SR570FullGainTable,
    SR570GainTable,
    SR570GainToCurrentTable,
    SR570RaiseTimeTable,
)
from dodal.devices.current_amplifiers.current_amplifier_detector import (
    CurrentAmpDet,
)
from dodal.devices.current_amplifiers.struck_scaler_counter import (
    CountState,
    StruckScaler,
)


@pytest.fixture
async def mock_sr570(prefix: str = "BLXX-EA-DET-007:", suffix: str = "Gain") -> SR570:
    async with init_devices(mock=True):
        mock_sr570 = SR570(
            prefix,
            suffix=suffix,
            fine_gain_table=SR570FineGainTable,
            coarse_gain_table=SR570GainTable,
            combined_table=SR570FullGainTable,
            gain_to_current_table=SR570GainToCurrentTable,
            raise_timetable=SR570RaiseTimeTable,
            upperlimit=4.7,
            lowerlimit=0.4,
            name="mock_sr570",
        )
    assert mock_sr570.name == "mock_sr570"
    return mock_sr570


@pytest.fixture
async def mock_StruckScaler(
    prefix: str = "BLXX-EA-DET-007:", suffix: str = ".s17"
) -> StruckScaler:
    async with init_devices(mock=True):
        mock_StruckScaler = StruckScaler(
            prefix=prefix,
            suffix=suffix,
            name="mock_StruckScaler",
        )
    assert mock_StruckScaler.name == "mock_StruckScaler"
    return mock_StruckScaler


@pytest.fixture
async def mock_sr570_struck_scaler_detector(
    mock_StruckScaler: StruckScaler,
    mock_sr570: SR570,
    prefix: str = "BLXX-EA-DET-007:",
) -> CurrentAmpDet:
    async with init_devices(mock=True):
        mock_sr570_struck_scaler_detector = CurrentAmpDet(
            current_amp=mock_sr570,
            counter=mock_StruckScaler,
            name="mock_sr570_struck_scaler_detector",
        )
    assert mock_sr570_struck_scaler_detector.name == "mock_sr570_struck_scaler_detector"
    return mock_sr570_struck_scaler_detector


@pytest.mark.parametrize(
    "gain, wait_time, gain_value",
    [
        ([1e3, 1e-4, "SEN_1"]),
        ([1e6, 1e-4, SR570FullGainTable.SEN_10.name]),
        ([2e6, 0.15, SR570FullGainTable.SEN_11.name]),
        ([2e7, 0.15, SR570FullGainTable.SEN_14.name]),
        ([2e9, 0.2, SR570FullGainTable.SEN_20.name]),
        ([1e12, 0.2, SR570FullGainTable.SEN_28.name]),
    ],
)
@mock.patch("asyncio.sleep")
async def test_sr570_set(
    sleep: AsyncMock, mock_sr570: SR570, RE: RunEngine, gain, wait_time, gain_value
):
    RE(abs_set(mock_sr570, gain, wait=True))
    assert (await mock_sr570.get_gain()).name == gain_value
    # extra sleeps either side of set are bluesky's sleep which are set to 0.
    for actual, expected in zip(
        sleep.call_args[0], [0, 0, wait_time, 0, 0], strict=False
    ):
        assert actual == expected


@pytest.mark.parametrize(
    "gain,",
    [
        (1e-2),
        (1),
        ("ssdfsden_212341"),
    ],
)
@mock.patch("asyncio.sleep")
async def test_sr570_set_fail_out_of_range(sleep: AsyncMock, mock_sr570: SR570, gain):
    with pytest.raises(ValueError) as e:
        await mock_sr570.set(gain)

    assert (
        str(e.value)
        == f"Gain value {gain} is not within {mock_sr570.name} range."
        + "\n Available gain:"
        + f" {[f'{c.value:.0e}' for c in mock_sr570.gain_conversion_table]}"
    )
    sleep.assert_not_called()


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        ([1e3, 1, 1e4]),
        ([5e3, 5, 5e8]),
        ([2e4, 3, 2e7]),
        ([1e5, 6, 1e11]),
    ],
)
@mock.patch("asyncio.sleep")
async def test_SR570_increase_gain(
    sleep: AsyncMock,
    mock_sr570: SR570,
    starting_gain: float,
    gain_change_count: int,
    final_gain: str,
):
    await mock_sr570.set(starting_gain)
    for _ in range(gain_change_count):
        await mock_sr570.increase_gain()
    assert (await mock_sr570.get_gain()) == SR570GainToCurrentTable(final_gain)
    assert sleep.call_count == gain_change_count + 1


@mock.patch("asyncio.sleep")
async def test_SR570_increase_gain_top_out_fail(
    sleep: AsyncMock,
    mock_sr570: SR570,
):
    starting_gain, final_gain = ["SEN_28", "SEN_28"]
    await mock_sr570.set(SR570GainToCurrentTable[starting_gain])
    with pytest.raises(ValueError):
        await mock_sr570.increase_gain()
    assert (await mock_sr570.get_gain()) == SR570GainToCurrentTable[final_gain]
    assert sleep.call_count == 2


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        ([1e8, 5, 1e3]),
        ([5e9, 3, 5e6]),
        ([2e11, 3, 2e8]),
        ([1e12, 8, 1e4]),
    ],
)
@mock.patch("asyncio.sleep")
async def test_SR570_decrease_gain(
    sleep: AsyncMock,
    mock_sr570: SR570,
    starting_gain: str,
    gain_change_count: int,
    final_gain: str,
):
    await mock_sr570.set(starting_gain)
    for _ in range(gain_change_count):
        await mock_sr570.decrease_gain()
    assert (await mock_sr570.get_gain()) == SR570GainToCurrentTable(final_gain)
    assert (
        sleep.call_count == gain_change_count + 1  # for starting gain
    )


@mock.patch("asyncio.sleep")
async def test_SR570_decrease_gain_bottom_out_fail(
    sleep: AsyncMock,
    mock_sr570: SR570,
):
    starting_gain, final_gain = ["SEN_1", "SEN_1"]
    await mock_sr570.set(SR570GainToCurrentTable[starting_gain])
    with pytest.raises(ValueError):
        await mock_sr570.decrease_gain()
    assert (await mock_sr570.get_gain()) == SR570GainToCurrentTable[final_gain]
    assert sleep.call_count == 2


class MockSR570RaiseTimeTable(float, Enum):
    """Mock raise time(s) for SR570 current amplifier to speed up test"""

    SEN_1 = 0
    SEN_2 = 0
    SEN_3 = 0
    SEN_4 = 0


@pytest.mark.parametrize(
    "gain,raw_count, expected_current",
    [
        ("SEN_1", 0.51e5, 0.51e-3),
        ("SEN_3", -10e5, -2e-3),
        ("SEN_11", 5.2e5, 2.6e-6),
        ("SEN_17", 2.2e5, 1.1e-8),
        ("SEN_23", 8.7e5, 4.35e-10),
        ("SEN_5", 0.0, 0.0),
    ],
)
async def test_SR570_struck_scaler_read(
    mock_sr570_struck_scaler_detector,
    RE: RunEngine,
    gain,
    raw_count,
    expected_current,
):
    temp = SR570FullGainTable[gain].value
    set_mock_value(mock_sr570_struck_scaler_detector.current_amp().coarse_gain, temp[0])
    set_mock_value(mock_sr570_struck_scaler_detector.current_amp().fine_gain, temp[1])
    set_mock_value(mock_sr570_struck_scaler_detector.counter().readout, raw_count)
    set_mock_value(mock_sr570_struck_scaler_detector.counter().count_time, 1)
    set_mock_value(mock_sr570_struck_scaler_detector.auto_mode, False)
    mock_sr570_struck_scaler_detector.current_amp().raise_timetable = (
        MockSR570RaiseTimeTable
    )
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(count([mock_sr570_struck_scaler_detector]), capture_emitted)
    assert docs["event"][0]["data"][
        "mock_sr570_struck_scaler_detector-current"
    ] == pytest.approx(expected_current)


@pytest.mark.parametrize(
    "gain,raw_count, expected_current",
    [
        (
            "SEN_10",
            [1e2, 1e3, 1e4, 1e5, 1e5],
            1e-9,
        ),
        ("SEN_1", [1e5, 1e5], 1e-3),
        (
            "SEN_10",
            [520e5, 52e5, 5.2e5, 5.2e4, 5.2e4],
            5.2e-4,
        ),
        ("SEN_19", [22.2e5, 2.22e5, 2.22e5], 2.22e-8),
        ("SEN_5", [0.0] * (30 - 5), 0.0),
        ("SEN_5", [-200.0e5, -20.0e5, -10.0e5, -10.0e5], -0.01),
        ("SEN_25", [0.002e5, 0.004e5, 0.01e5, 0.02e5, 0.02e5], 2e-14),
    ],
)
async def test_SR570_struck_scaler_read_with_autoGain(
    mock_sr570_struck_scaler_detector,
    RE: RunEngine,
    gain,
    raw_count,
    expected_current,
):
    mock_sr570_struck_scaler_detector.current_amp().raise_timetable = (
        MockSR570RaiseTimeTable
    )
    await mock_sr570_struck_scaler_detector.current_amp().set(
        SR570GainToCurrentTable[gain]
    )
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

    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(prepare(mock_sr570_struck_scaler_detector, 1))
    RE(count([mock_sr570_struck_scaler_detector]), capture_emitted)
    assert docs["event"][0]["data"][
        "mock_sr570_struck_scaler_detector-current"
    ] == pytest.approx(expected_current, rel=1e-14)
