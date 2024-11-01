from collections import defaultdict
from unittest import mock
from unittest.mock import AsyncMock

import pytest
from bluesky.plan_stubs import abs_set
from bluesky.plans import count
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, get_mock_put, set_mock_value

from dodal.devices.current_amplifiers import (
    Femto3xxGainTable,
    Femto3xxRaiseTime,
    FemtoAdcDetector,
    FemtoDDPCA,
)


@pytest.fixture
async def mock_femto(
    prefix: str = "BLXX-EA-DET-007:", suffix: str = "Gain"
) -> FemtoDDPCA:
    async with DeviceCollector(mock=True):
        mock_femto = FemtoDDPCA(
            prefix=prefix,
            suffix=suffix,
            gain_table=Femto3xxGainTable,
            raise_timetable=Femto3xxRaiseTime,
            name="mock_femto",
        )
    assert mock_femto.name == "mock_femto"
    return mock_femto


@pytest.fixture
async def mock_femto_adc_detector(
    mock_femto: FemtoDDPCA,
    prefix: str = "BLXX-EA-DET-007:",
) -> FemtoAdcDetector:
    async with DeviceCollector(mock=True):
        mock_femto_adc_detector = FemtoAdcDetector(
            prefix=prefix,
            current_amp=mock_femto,
            name="mock_femto_adc_detector",
        )
    assert mock_femto_adc_detector.name == "mock_femto_adc_detector"
    return mock_femto_adc_detector


@pytest.mark.parametrize(
    "gain, wait_time, gain_value",
    [
        (["sen_1", 0.8e-3, "10^4"]),
        (["sen_3", 0.8e-3, "10^6"]),
        (["sen_5", 2.3e-3, "10^8"]),
        (["sen_7", 17e-3, "10^10"]),
        (["sen_10", 350e-3, "10^13"]),
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
async def test_femto_adc_detector_read(
    mock_femto: FemtoDDPCA,
    mock_femto_adc_detector: FemtoAdcDetector,
    RE: RunEngine,
    gain,
    raw_voltage,
    expected_current,
):
    set_mock_value(mock_femto.gain, Femto3xxGainTable[gain])
    set_mock_value(mock_femto_adc_detector.analogue_readout, raw_voltage)
    set_mock_value(mock_femto_adc_detector.auto_mode, False)
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(count([mock_femto_adc_detector]), capture_emitted)
    assert docs["event"][0]["data"]["mock_femto_adc_detector-current"] == pytest.approx(
        expected_current
    )
