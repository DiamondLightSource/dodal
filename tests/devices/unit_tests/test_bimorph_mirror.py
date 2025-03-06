from unittest.mock import ANY, call, patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import get_mock_put

from dodal.devices.bimorph_mirror import BimorphMirror, BimorphMirrorStatus

VALID_BIMORPH_CHANNELS = [8, 12, 16, 24]


@pytest.fixture
def mirror(request, RE: RunEngine) -> BimorphMirror:
    number_of_channels = request.param

    with init_devices(mock=True):
        bm = BimorphMirror(
            prefix="FAKE-PREFIX:",
            number_of_channels=number_of_channels,
        )

    return bm


@pytest.fixture
def valid_bimorph_values(mirror: BimorphMirror) -> dict[int, float]:
    return {i: float(i) for i in range(1, len(mirror.channels) + 1)}


@pytest.fixture
def mock_vtrgt_vout_propogation(mirror: BimorphMirror):
    for channel in mirror.channels.values():

        def effect(value: float, wait=False, signal=channel.output_voltage):
            signal.set(value, wait=wait)

        get_mock_put(channel.target_voltage).side_effect = effect


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_set_channels_waits_for_readback(
    mirror: BimorphMirror,
    valid_bimorph_values: dict[int, float],
    mock_vtrgt_vout_propogation,
):
    await mirror.set(valid_bimorph_values)

    assert {
        key: await mirror.channels[key].target_voltage.get_value()
        for key in valid_bimorph_values
    } == valid_bimorph_values


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_set_channels_triggers_alltrgt_proc(
    mirror: BimorphMirror,
    valid_bimorph_values: dict[int, float],
    mock_vtrgt_vout_propogation,
):
    mock_alltrgt_proc = get_mock_put(mirror.commit_target_voltages)

    mock_alltrgt_proc.assert_not_called()

    await mirror.set(valid_bimorph_values)

    mock_alltrgt_proc.assert_called_once()


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_set_channels_waits_for_vout_readback(
    mirror: BimorphMirror,
    valid_bimorph_values: dict[int, float],
    mock_vtrgt_vout_propogation,
):
    with patch("dodal.devices.bimorph_mirror.wait_for_value") as mock_wait_for_value:
        mock_wait_for_value.assert_not_called()

        await mirror.set(valid_bimorph_values)

        expected_call_arg_list = [
            call(mirror.channels[i].output_voltage, ANY, timeout=ANY)
            for i, val in valid_bimorph_values.items()
        ]
        expected_call_arg_list.append(
            call(mirror.status, BimorphMirrorStatus.IDLE, timeout=ANY)
        )
        assert expected_call_arg_list == mock_wait_for_value.call_args_list


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_set_channels_allows_tolerance(
    mirror: BimorphMirror,
    valid_bimorph_values: dict[int, float],
):
    for channel in mirror.channels.values():

        def out_by_a_little(value: float, wait=False, signal=channel.output_voltage):
            signal.set(value + 0.00001, wait=wait)

        get_mock_put(channel.target_voltage).side_effect = out_by_a_little

    await mirror.set(valid_bimorph_values)


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_set_one_channel(mirror: BimorphMirror, mock_vtrgt_vout_propogation):
    values = {1: 1}

    await mirror.set(values)

    read = await mirror.read()

    assert [
        await mirror.channels[key].target_voltage.get_value() for key in values
    ] == list(values)

    assert [
        read[f"{mirror.name}-channels-{key}-output_voltage"]["value"] for key in values
    ] == list(values)


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_read(
    mirror: BimorphMirror,
    valid_bimorph_values: dict[int, float],
    mock_vtrgt_vout_propogation,
):
    await mirror.set(valid_bimorph_values)

    read = await mirror.read()

    assert [
        read[f"{mirror.name}-channels-{i}-output_voltage"]["value"]
        for i in range(1, len(mirror.channels) + 1)
    ] == list(valid_bimorph_values.values())


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_set_invalid_channel_throws_error(mirror: BimorphMirror):
    with pytest.raises(ValueError):
        await mirror.set({len(mirror.channels) + 1: 0.0})


@pytest.mark.parametrize("number_of_channels", [-1])
async def test_init_mirror_with_invalid_channels_throws_error(number_of_channels):
    with pytest.raises(ValueError):
        BimorphMirror(prefix="FAKE-PREFIX:", number_of_channels=number_of_channels)


@pytest.mark.parametrize("number_of_channels", [0])
async def test_init_mirror_with_zero_channels(number_of_channels):
    mirror = BimorphMirror(prefix="FAKE-PREFIX", number_of_channels=number_of_channels)
    assert len(mirror.channels) == 0


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_bimorph_mirror_channel_set(
    mirror: BimorphMirror,
    valid_bimorph_values: dict[int, float],
):
    for value, channel in zip(
        valid_bimorph_values.values(), mirror.channels.values(), strict=True
    ):
        assert await channel.output_voltage.get_value() != value
        await channel.set(value)
        assert await channel.output_voltage.get_value() == value
