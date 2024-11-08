from collections import defaultdict
from unittest import mock
from unittest.mock import AsyncMock, Mock

import pytest
from bluesky.plan_stubs import abs_set
from bluesky.plans import count
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DeviceCollector,
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.current_amplifiers import (
    Femto3xxGainTable,
    Femto3xxGainToCurrentTable,
    Femto3xxRaiseTime,
    FemtoDDPCA,
)
from dodal.devices.current_amplifiers.amp_detector import AutoGainDectector
from dodal.devices.current_amplifiers.struck_scaler import CountState, StruckScaler


@pytest.fixture
async def mock_femto(
    prefix: str = "BLXX-EA-DET-007:", suffix: str = "Gain"
) -> FemtoDDPCA:
    async with DeviceCollector(mock=True):
        mock_femto = FemtoDDPCA(
            prefix=prefix,
            suffix=suffix,
            gain_table=Femto3xxGainTable,
            gain_to_current_table=Femto3xxGainToCurrentTable,
            raise_timetable=Femto3xxRaiseTime,
            name="mock_femto",
        )
    assert mock_femto.name == "mock_femto"
    return mock_femto


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
async def mock_femto_struck_scaler_detector(
    mock_StruckScaler: StruckScaler,
    mock_femto: FemtoDDPCA,
    prefix: str = "BLXX-EA-DET-007:",
) -> AutoGainDectector:
    async with DeviceCollector(mock=True):
        mock_femto_struck_scaler_detector = AutoGainDectector(
            current_amp=mock_femto,
            counter=mock_StruckScaler,
            upper_limit=9.5,
            lower_limit=0.5,
            name="mock_femto_struck_scaler_detector",
        )
    assert mock_femto_struck_scaler_detector.name == "mock_femto_struck_scaler_detector"
    return mock_femto_struck_scaler_detector


@pytest.mark.parametrize(
    "gain, wait_time, gain_value",
    [
        ([1e4, 0.8e-3, "10^4"]),
        ([1e6, 0.8e-3, "10^6"]),
        ([1e8, 2.3e-3, "10^8"]),
        ([1e10, 17e-3, "10^10"]),
        ([1e13, 350e-3, "10^13"]),
    ],
)
@mock.patch("asyncio.sleep")
async def test_femto_set(
    sleep: AsyncMock, mock_femto: FemtoDDPCA, RE: RunEngine, gain, wait_time, gain_value
):
    RE(abs_set(mock_femto, gain, wait=True))
    assert await mock_femto.gain.get_value() == gain_value
    # extra sleeps either side of set are bluesky's sleep which are set to 0.
    for actual, expected in zip(
        sleep.call_args[0], [0, 0, wait_time, 0, 0], strict=False
    ):
        assert actual == expected


@pytest.mark.parametrize(
    "gain,",
    [
        ("sen_0"),
        ("sen_24"),
        ("ssdfsden_212341"),
    ],
)
@mock.patch("asyncio.sleep")
async def test_femto_set_fail_out_of_range(
    sleep: AsyncMock, mock_femto: FemtoDDPCA, gain
):
    with pytest.raises(ValueError) as e:
        await mock_femto.set(gain)
    assert str(e.value) == f"Gain value {gain} is not within {mock_femto.name} range."
    get_mock_put(mock_femto.gain).assert_not_called()
    sleep.assert_not_called()


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        (["sen_1", 1, "sen_2"]),
        (["sen_3", 5, "sen_8"]),
        (["sen_5", 3, "sen_8"]),
        (["sen_7", 20, "sen_10"]),
    ],
)
@mock.patch("asyncio.sleep")
async def test_femto_increase_gain(
    sleep: AsyncMock,
    mock_femto: FemtoDDPCA,
    starting_gain: str,
    gain_change_count: int,
    final_gain: str,
):
    set_mock_value(mock_femto.gain, Femto3xxGainTable[starting_gain])
    for _ in range(gain_change_count):
        await mock_femto.increase_gain()
    assert (await mock_femto.gain.get_value()) == Femto3xxGainTable[final_gain]
    assert sleep.call_count == int(final_gain.split("_")[-1]) - int(
        starting_gain.split("_")[-1]
    )


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        (["sen_1", 5, "sen_1"]),
        (["sen_6", 2, "sen_4"]),
        (["sen_8", 3, "sen_5"]),
        (["sen_7", 20, "sen_1"]),
    ],
)
@mock.patch("asyncio.sleep")
async def test_femto_decrease_gain(
    sleep: AsyncMock,
    mock_femto: FemtoDDPCA,
    starting_gain: str,
    gain_change_count: int,
    final_gain: str,
):
    set_mock_value(mock_femto.gain, Femto3xxGainTable[starting_gain])
    for _ in range(gain_change_count):
        await mock_femto.decrease_gain()
    assert (await mock_femto.gain.get_value()) == Femto3xxGainTable[final_gain]
    assert sleep.call_count == int(starting_gain.split("_")[-1]) - int(
        final_gain.split("_")[-1]
    )


@pytest.mark.parametrize(
    "gain,raw_voltage, expected_current",
    [
        ("sen_1", 0.51, 0.51e-4),
        ("sen_3", -10, -10e-6),
        ("sen_6", 5.2, 5.2e-9),
        ("sen_9", 2.2, 2.2e-12),
        ("sen_10", 8.7, 8.7e-13),
        ("sen_5", 0.0, 0.0),
    ],
)
async def test_femto_struck_scaler_read(
    mock_femto: FemtoDDPCA,
    mock_femto_struck_scaler_detector: AutoGainDectector,
    RE: RunEngine,
    gain,
    raw_voltage,
    expected_current,
):
    set_mock_value(mock_femto.gain, Femto3xxGainTable[gain])
    set_mock_value(mock_femto_struck_scaler_detector.counter.readout, raw_voltage)
    set_mock_value(mock_femto_struck_scaler_detector.auto_mode, False)
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(count([mock_femto_struck_scaler_detector]), capture_emitted)
    assert docs["event"][0]["data"][
        "mock_femto_struck_scaler_detector-current"
    ] == pytest.approx(expected_current)


@pytest.mark.parametrize(
    "gain,raw_voltage, expected_current",
    [
        ("sen_10", [1e4, 1e3, 1e2, 1e1, 1], 1e-9),
        ("sen_1", [4e-3, 4e-2, 4e-1, 4], 4e-7),
        ("sen_6", [520, 52, 5.2], 5.2e-7),
        ("sen_9", [2.2, 2.2], 2.2e-12),
        ("sen_10", [0.17, 0.17], 0.17e-13),
        ("sen_5", [0.0, 0.0], 0.0),
        ("sen_5", [-200.0, -20.0, -2.0], -2e-6),
    ],
)
async def test_femto_struck_scaler_read_with_autoGain(
    mock_femto: FemtoDDPCA,
    mock_femto_struck_scaler_detector: AutoGainDectector,
    RE: RunEngine,
    gain,
    raw_voltage,
    expected_current,
):
    set_mock_value(mock_femto.gain, Femto3xxGainTable[gain])
    set_mock_value(mock_femto_struck_scaler_detector.counter.count_time, 1)
    set_mock_value(mock_femto_struck_scaler_detector.auto_mode, True)
    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = raw_voltage

    def set_mock_counter():
        set_mock_value(
            mock_femto_struck_scaler_detector.counter.trigger_start, CountState.done
        )
        set_mock_value(
            mock_femto_struck_scaler_detector.counter.readout, rbv_mocks.get()
        )

    callback_on_mock_put(
        mock_femto_struck_scaler_detector.counter.trigger_start,
        lambda *_, **__: set_mock_counter(),
    )

    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(count([mock_femto_struck_scaler_detector]), capture_emitted)
    assert docs["event"][0]["data"][
        "mock_femto_struck_scaler_detector-current"
    ] == pytest.approx(expected_current, rel=1e-14)
