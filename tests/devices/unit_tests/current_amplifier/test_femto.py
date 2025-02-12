from collections import defaultdict
from enum import Enum
from unittest import mock
from unittest.mock import AsyncMock, Mock

import pytest
from bluesky.plan_stubs import abs_set
from bluesky.plans import count
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import (
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
from dodal.devices.current_amplifiers.current_amplifier_detector import (
    CurrentAmpDet,
)
from dodal.devices.current_amplifiers.struck_scaler_counter import (
    CountState,
    StruckScaler,
)


@pytest.fixture
async def mock_femto(
    prefix: str = "BLXX-EA-DET-007:", suffix: str = "Gain"
) -> FemtoDDPCA:
    async with init_devices(mock=True):
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
    async with init_devices(mock=True):
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
) -> CurrentAmpDet:
    async with init_devices(mock=True):
        mock_femto_struck_scaler_detector = CurrentAmpDet(
            current_amp=mock_femto,
            counter=mock_StruckScaler,
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
        ("SEN_0"),
        ("SEN_24"),
        ("ssdfsden_212341"),
    ],
)
@mock.patch("asyncio.sleep")
async def test_femto_set_fail_out_of_range(
    sleep: AsyncMock, mock_femto: FemtoDDPCA, gain
):
    with pytest.raises(ValueError) as e:
        await mock_femto.set(gain)
    assert (
        str(e.value)
        == f"Gain value {gain} is not within {mock_femto.name} range."
        + "\n Available gain:"
        + f" {[f'{c.value:.0e}' for c in mock_femto.gain_conversion_table]}"
    )
    get_mock_put(mock_femto.gain).assert_not_called()
    sleep.assert_not_called()


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        (["SEN_1", 1, "SEN_2"]),
        (["SEN_3", 5, "SEN_8"]),
        (["SEN_5", 3, "SEN_8"]),
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


@mock.patch("asyncio.sleep")
async def test_femto_increase_gain_fail_at_max_gain(
    sleep: AsyncMock,
    mock_femto: FemtoDDPCA,
):
    starting_gain, final_gain = ["SEN_10", "SEN_10"]
    set_mock_value(mock_femto.gain, Femto3xxGainTable[starting_gain])
    with pytest.raises(ValueError):
        await mock_femto.increase_gain()
    assert (await mock_femto.gain.get_value()) == Femto3xxGainTable[final_gain]
    assert sleep.call_count == int(final_gain.split("_")[-1]) - int(
        starting_gain.split("_")[-1]
    )


@pytest.mark.parametrize(
    "starting_gain, gain_change_count, final_gain",
    [
        (["SEN_6", 2, "SEN_4"]),
        (["SEN_8", 3, "SEN_5"]),
        (["SEN_10", 9, "SEN_1"]),
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


@mock.patch("asyncio.sleep")
async def test_femto_decrease_gain_fail_at_min_gain(
    sleep: AsyncMock,
    mock_femto: FemtoDDPCA,
):
    starting_gain, final_gain = ["SEN_1", "SEN_1"]
    set_mock_value(mock_femto.gain, Femto3xxGainTable[starting_gain])
    with pytest.raises(ValueError):
        await mock_femto.decrease_gain()
    assert (await mock_femto.gain.get_value()) == Femto3xxGainTable[final_gain]
    assert sleep.call_count == int(final_gain.split("_")[-1]) - int(
        starting_gain.split("_")[-1]
    )


class MockFemto3xxRaiseTime(float, Enum):
    """Mock zero raise time(s) for Femto 3xx current amplifier"""

    SEN_1 = 0.0
    SEN_2 = 0.0
    SEN_3 = 0.0
    SEN_4 = 0.0
    SEN_5 = 0.0
    SEN_6 = 0.0
    SEN_7 = 0.0
    SEN_8 = 0.0
    SEN_9 = 0.0
    SEN_10 = 0.0


@pytest.mark.parametrize(
    "gain,raw_voltage, expected_current",
    [
        ("SEN_1", 0.51e5, 0.51e-4),
        ("SEN_3", -10e5, -10e-6),
        ("SEN_6", 5.2e5, 5.2e-9),
        ("SEN_9", 2.2e5, 2.2e-12),
        ("SEN_10", 8.7e5, 8.7e-13),
        ("SEN_5", 0.0, 0.0),
    ],
)
async def test_femto_struck_scaler_read(
    mock_femto: FemtoDDPCA,
    mock_femto_struck_scaler_detector,
    RE: RunEngine,
    gain,
    raw_voltage,
    expected_current,
):
    set_mock_value(mock_femto.gain, Femto3xxGainTable[gain])
    set_mock_value(mock_femto_struck_scaler_detector.counter().count_time, 1)
    set_mock_value(mock_femto_struck_scaler_detector.counter().readout, raw_voltage)
    set_mock_value(mock_femto_struck_scaler_detector.auto_mode, False)
    docs = defaultdict(list)
    mock_femto_struck_scaler_detector.current_amp().raise_timetable = (
        MockFemto3xxRaiseTime
    )

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(count([mock_femto_struck_scaler_detector]), capture_emitted)
    assert docs["event"][0]["data"][
        "mock_femto_struck_scaler_detector-current"
    ] == pytest.approx(expected_current)


@pytest.mark.parametrize(
    "gain,raw_voltage, expected_current",
    [
        ("SEN_10", [1e9, 1e8, 1e7, 1e6] + [1e5] * 2, 1e-9),
        ("SEN_1", [4e2, 4e3, 4e4] + [4e5] * 2, 4e-7),
        ("SEN_6", [520e5, 52e5, 5.2e5, 5.2e5], 5.2e-7),
        ("SEN_9", [2.2e5, 2.2e5], 2.2e-12),
        ("SEN_10", [0.17e5, 0.17e5], 0.17e-13),
        ("SEN_5", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0.0),
        ("SEN_5", [-200.0e5, -20.0e5, -2.0e5, -2.0e5], -2e-6),
        ("SEN_1", [10.0e-6] * (30), 1.0e-23),
    ],
)
async def test_femto_struck_scaler_read_with_autoGain(
    mock_femto: FemtoDDPCA,
    mock_femto_struck_scaler_detector,
    RE: RunEngine,
    gain,
    raw_voltage,
    expected_current,
):
    set_mock_value(mock_femto.gain, Femto3xxGainTable[gain])
    set_mock_value(mock_femto_struck_scaler_detector.counter().count_time, 1)
    set_mock_value(mock_femto_struck_scaler_detector.auto_mode, True)
    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = raw_voltage
    mock_femto_struck_scaler_detector.current_amp().raise_timetable = (
        MockFemto3xxRaiseTime
    )

    def set_mock_counter():
        set_mock_value(
            mock_femto_struck_scaler_detector.counter().trigger_start, CountState.DONE
        )
        set_mock_value(
            mock_femto_struck_scaler_detector.counter().readout, rbv_mocks.get()
        )

    callback_on_mock_put(
        mock_femto_struck_scaler_detector.counter().trigger_start,
        lambda *_, **__: set_mock_counter(),
    )

    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(count([mock_femto_struck_scaler_detector]), capture_emitted)
    assert docs["event"][0]["data"][
        "mock_femto_struck_scaler_detector-current"
    ] == pytest.approx(expected_current, rel=1e-14)
