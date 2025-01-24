import asyncio
from typing import Any
from unittest.mock import ANY, call, patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, SignalRW, walk_rw_signals
from ophyd_async.testing import callback_on_mock_put, get_mock_put, set_mock_value

from dodal.devices.bimorph_mirror import BimorphMirror, BimorphMirrorStatus

VALID_BIMORPH_CHANNELS = [8, 12, 16, 24]


@pytest.fixture(params=VALID_BIMORPH_CHANNELS)
def mirror(request, RE: RunEngine) -> BimorphMirror:
    number_of_channels = request.param

    with DeviceCollector(mock=True):
        bm = BimorphMirror(
            prefix="FAKE-PREFIX:",
            number_of_channels=number_of_channels,
        )

    return bm


@pytest.fixture
def valid_bimorph_values(mirror: BimorphMirror) -> dict[int, float]:
    return {i: float(i) for i in range(1, len(mirror.channels) + 1)}


@pytest.fixture
def mirror_with_mocked_put(mirror: BimorphMirror):
    async def busy_idle():
        await asyncio.sleep(0)
        set_mock_value(mirror.status, BimorphMirrorStatus.BUSY)
        await asyncio.sleep(0)
        set_mock_value(mirror.status, BimorphMirrorStatus.IDLE)

    async def status(*_: Any, **__: Any):
        asyncio.create_task(busy_idle())

    for signal in walk_rw_signals(mirror).values():
        callback_on_mock_put(signal, status)

    for channel in mirror.channels.values():

        def vout_propogation_and_status(
            value: float,
            wait: bool = False,
            signal: SignalRW[float] = channel.output_voltage,
        ):
            signal.set(value, wait=wait)
            asyncio.create_task(busy_idle())

        callback_on_mock_put(channel.target_voltage, vout_propogation_and_status)

    return mirror


async def test_set_channels_waits_for_readback(
    mirror_with_mocked_put: BimorphMirror,
    valid_bimorph_values: dict[int, float],
):
    await mirror_with_mocked_put.set(valid_bimorph_values)

    assert {
        key: await mirror_with_mocked_put.channels[key].target_voltage.get_value()
        for key in valid_bimorph_values
    } == valid_bimorph_values


async def test_set_channels_triggers_alltrgt_proc(
    mirror_with_mocked_put: BimorphMirror,
    valid_bimorph_values: dict[int, float],
):
    mock_alltrgt_proc = get_mock_put(mirror_with_mocked_put.commit_target_voltages)

    mock_alltrgt_proc.assert_not_called()

    await mirror_with_mocked_put.set(valid_bimorph_values)

    mock_alltrgt_proc.assert_called_once()


async def test_set_channels_waits_for_vout_readback(
    mirror_with_mocked_put: BimorphMirror,
    valid_bimorph_values: dict[int, float],
):
    with patch("dodal.devices.bimorph_mirror.wait_for_value") as mock_wait_for_value:
        mock_wait_for_value.assert_not_called()

        await mirror_with_mocked_put.set(valid_bimorph_values)

        expected_call_arg_list = [
            call(mirror_with_mocked_put.channels[i].output_voltage, ANY, timeout=ANY)
            for i, val in valid_bimorph_values.items()
        ]

        assert all(
            c in mock_wait_for_value.call_args_list for c in expected_call_arg_list
        )


async def test_set_one_channel(mirror_with_mocked_put: BimorphMirror):
    values = {1: 1}

    await mirror_with_mocked_put.set(values)

    read = await mirror_with_mocked_put.read()

    assert [
        await mirror_with_mocked_put.channels[key].target_voltage.get_value()
        for key in values
    ] == list(values)

    assert [
        read[f"{mirror_with_mocked_put.name}-channels-{key}-output_voltage"]["value"]
        for key in values
    ] == list(values)


async def test_read(
    mirror_with_mocked_put: BimorphMirror,
    valid_bimorph_values: dict[int, float],
):
    await mirror_with_mocked_put.set(valid_bimorph_values)

    read = await mirror_with_mocked_put.read()

    assert [
        read[f"{mirror_with_mocked_put.name}-channels-{i}-output_voltage"]["value"]
        for i in range(1, len(mirror_with_mocked_put.channels) + 1)
    ] == list(valid_bimorph_values.values())


async def test_set_invalid_channel_throws_error(mirror_with_mocked_put: BimorphMirror):
    with pytest.raises(ValueError):
        await mirror_with_mocked_put.set(
            {len(mirror_with_mocked_put.channels) + 1: 0.0}
        )


@pytest.mark.parametrize("number_of_channels", [-1])
async def test_init_mirror_with_invalid_channels_throws_error(number_of_channels):
    with pytest.raises(ValueError):
        BimorphMirror(prefix="FAKE-PREFIX:", number_of_channels=number_of_channels)


@pytest.mark.parametrize("number_of_channels", [0])
async def test_init_mirror_with_zero_channels(number_of_channels):
    mirror_with_mocked_put = BimorphMirror(
        prefix="FAKE-PREFIX", number_of_channels=number_of_channels
    )
    assert len(mirror_with_mocked_put.channels) == 0


async def test_bimorph_mirror_channel_set(
    mirror_with_mocked_put: BimorphMirror,
    valid_bimorph_values: dict[int, float],
):
    for value, channel in zip(
        valid_bimorph_values.values(),
        mirror_with_mocked_put.channels.values(),
        strict=True,
    ):
        assert await channel.output_voltage.get_value() != value
        await channel.set(value)
        assert await channel.output_voltage.get_value() == value
