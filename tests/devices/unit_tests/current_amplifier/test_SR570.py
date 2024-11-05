from collections import defaultdict
from unittest import mock
from unittest.mock import AsyncMock, Mock

import pytest
from bluesky.plan_stubs import abs_set
from bluesky.plans import count
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DeviceCollector,
    StrictEnum,
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.current_amplifiers import (
    SR570,
    SR570FineGainTable,
    SR570FullGainTable,
    SR570GainTable,
    SR570GainToCurrentTable,
    SR570RaiseTimeTable,
)
from dodal.devices.current_amplifiers.amp_detector import AutoGainDectector
from dodal.devices.current_amplifiers.struck_scaler import CountState, StruckScaler


@pytest.fixture
async def mock_sr570(prefix: str = "BLXX-EA-DET-007:", suffix: str = "Gain") -> SR570:
    async with DeviceCollector(mock=True):
        mock_sr570 = SR570(
            prefix=prefix,
            suffix=suffix,
            gain_table=SR570GainTable,
            fine_gain_table=SR570FineGainTable,
            full_gain_table=SR570FullGainTable,
            gain_to_current_table=SR570GainToCurrentTable,
            raise_timetable=SR570RaiseTimeTable,
            name="mock_sr570",
        )
    assert mock_sr570.name == "mock_sr570"
    return mock_sr570


@pytest.fixture
async def mock_StruckScaler(
    prefix: str = "BLXX-EA-DET-007:", suffix: str = ".s17"
) -> StruckScaler:
    async with DeviceCollector(mock=True):
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
) -> AutoGainDectector:
    async with DeviceCollector(mock=True):
        mock_sr570_struck_scaler_detector = AutoGainDectector(
            current_amp=mock_sr570,
            counter=mock_StruckScaler,
            upper_limit=4.7,
            lower_limit=0.4,
            name="mock_sr570_struck_scaler_detector",
        )
    assert mock_sr570_struck_scaler_detector.name == "mock_sr570_struck_scaler_detector"
    return mock_sr570_struck_scaler_detector


@pytest.mark.parametrize(
    "gain, wait_time, gain_value",
    [
        (["sen_1", 1e-4, SR570FullGainTable.sen_1]),
        (["sen_10", 1e-4, SR570FullGainTable.sen_10]),
        (["sen_11", 0.15, SR570FullGainTable.sen_11]),
        (["sen_14", 0.15, SR570FullGainTable.sen_14]),
        (["sen_20", 0.2, SR570FullGainTable.sen_20]),
        (["sen_28", 0.2, SR570FullGainTable.sen_28]),
    ],
)
@mock.patch("asyncio.sleep")
async def test_sr570_set(
    sleep: AsyncMock, mock_sr570: SR570, RE: RunEngine, gain, wait_time, gain_value
):
    RE(abs_set(mock_sr570, gain, wait=True))
    assert await mock_sr570.gain.get_value() == gain_value
    # extra sleeps either side of set are bluesky's sleep which are set to 0.
    for actual, expected in zip(
        sleep.call_args[0], [0, 0, wait_time, 0, 0], strict=False
    ):
        assert actual == expected


@pytest.mark.parametrize(
    "gain,",
    [
        ("sen_0"),
        ("sen_29"),
        ("ssdfsden_212341"),
    ],
)
@mock.patch("asyncio.sleep")
async def test_sr570_set_fail_out_of_range(sleep: AsyncMock, mock_sr570: SR570, gain):
    with pytest.raises(ValueError) as e:
        await mock_sr570.set(gain)
    assert str(e.value) == f"Gain value {gain} is not within {mock_sr570.name} range."
    get_mock_put(mock_sr570.gain).assert_not_called()
    sleep.assert_not_called()


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        (["sen_1", 1, "sen_2"]),
        (["sen_3", 5, "sen_8"]),
        (["sen_5", 3, "sen_8"]),
        (["sen_7", 20, "sen_27"]),
        (["sen_26", 5, "sen_28"]),
    ],
)
@mock.patch("asyncio.sleep")
async def test_SR570_increase_gain(
    sleep: AsyncMock,
    mock_sr570: SR570,
    starting_gain: str,
    gain_change_count: int,
    final_gain: str,
):
    set_mock_value(mock_sr570.gain, SR570FullGainTable[starting_gain])
    for _ in range(gain_change_count):
        await mock_sr570.increase_gain()
    assert (await mock_sr570.gain.get_value()) == SR570FullGainTable[final_gain]
    assert sleep.call_count == int(final_gain.split("_")[-1]) - int(
        starting_gain.split("_")[-1]
    )


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        (["sen_1", 5, "sen_1"]),
        (["sen_6", 2, "sen_4"]),
        (["sen_8", 3, "sen_5"]),
        (["sen_28", 13, "sen_15"]),
        (["sen_7", 20, "sen_1"]),
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
    set_mock_value(mock_sr570.gain, SR570FullGainTable[starting_gain])
    for _ in range(gain_change_count):
        await mock_sr570.decrease_gain()
    assert (await mock_sr570.gain.get_value()) == SR570FullGainTable[final_gain]
    assert sleep.call_count == int(starting_gain.split("_")[-1]) - int(
        final_gain.split("_")[-1]
    )


@pytest.mark.parametrize(
    "gain,raw_voltage, expected_current",
    [
        ("sen_1", 0.51, 0.51e-3),
        ("sen_3", -10, -2e-3),
        ("sen_11", 5.2, 2.6e-6),
        ("sen_17", 2.2, 1.1e-8),
        ("sen_23", 8.7, 4.35e-9),
        ("sen_5", 0.0, 0.0),
    ],
)
async def test_SR570_struck_scaler_read(
    mock_sr570: SR570,
    mock_sr570_struck_scaler_detector: AutoGainDectector,
    RE: RunEngine,
    gain,
    raw_voltage,
    expected_current,
):
    set_mock_value(mock_sr570.gain, SR570FullGainTable[gain])
    set_mock_value(mock_sr570_struck_scaler_detector.counter.readout, raw_voltage)
    set_mock_value(mock_sr570_struck_scaler_detector.auto_mode, False)
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(count([mock_sr570_struck_scaler_detector]), capture_emitted)
    assert docs["event"][0]["data"][
        "mock_sr570_struck_scaler_detector-current"
    ] == pytest.approx(expected_current)


@pytest.mark.parametrize(
    "gain,raw_voltage, expected_current",
    [
        (
            "sen_10",
            [1e-3, 2e-3, 5e-3, 1e-2, 2e-2, 5e-2, 1e-1, 2e-1, 5e-1, 5e-1],
            1e-9,
        ),
        ("sen_1", [1, 1], 1e-3),
        ("sen_10", [520, 260, 104, 52, 26, 10.4, 5.2, 2.6, 2.6], 5.2e-4),
        ("sen_19", [22.2, 11.1, 4.4, 4.4], 2.2e-8),
        ("sen_5", [0.0, 0.0], 0.0),
        ("sen_5", [-200.0, -100.0, -50.0, -20, -10, -10], -0.01),
        ("sen_25", [0.002, 0.004, 0.01, 0.02, 0.02], 2e-14),
    ],
)
async def test_SR570_struck_scaler_read_with_autoGain(
    mock_sr570: SR570,
    mock_sr570_struck_scaler_detector: AutoGainDectector,
    RE: RunEngine,
    gain,
    raw_voltage,
    expected_current,
):
    set_mock_value(mock_sr570.gain, StrictEnum(SR570FullGainTable[gain]))
    set_mock_value(mock_sr570_struck_scaler_detector.counter.count_time, 1)
    set_mock_value(mock_sr570_struck_scaler_detector.auto_mode, True)
    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = raw_voltage

    def set_mock_counter():
        set_mock_value(
            mock_sr570_struck_scaler_detector.counter.trigger_start, CountState.done
        )
        set_mock_value(
            mock_sr570_struck_scaler_detector.counter.readout, rbv_mocks.get()
        )

    callback_on_mock_put(
        mock_sr570_struck_scaler_detector.counter.trigger_start,
        lambda *_, **__: set_mock_counter(),
    )

    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(count([mock_sr570_struck_scaler_detector]), capture_emitted)
    assert docs["event"][0]["data"][
        "mock_sr570_struck_scaler_detector-current"
    ] == pytest.approx(expected_current, rel=1e-14)
