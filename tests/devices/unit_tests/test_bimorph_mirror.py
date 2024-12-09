from unittest.mock import ANY, call, patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, get_mock_put, set_mock_value

from dodal.devices.bimorph_mirror import BimorphMirror

VALID_BIMORPH_CHANNELS = [8, 12, 16, 24]


@pytest.fixture
def mirror(request, RE: RunEngine) -> BimorphMirror:
    number_of_channels = request.param

    with DeviceCollector(mock=True):
        bm = BimorphMirror(
            prefix="BL02J-EA-IOC-97:G0:",
            number_of_channels=number_of_channels,
        )

    return bm


@pytest.fixture
def valid_bimorph_values(mirror: BimorphMirror) -> dict[int, float]:
    return {i: float(i) for i in range(1, mirror.number_of_channels + 1)}


@pytest.fixture
def set_vout_mock(valid_bimorph_values: dict[int, float], mirror: BimorphMirror):
    for key, val in valid_bimorph_values.items():
        set_mock_value(mirror.channels[key].vout, val)


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_set_channels_waits_for_readback(
    mirror: BimorphMirror, valid_bimorph_values: dict[int, float], set_vout_mock
):
    await mirror.set(valid_bimorph_values)

    assert {
        key: await mirror.channels[key].vtrgt.get_value()
        for key in valid_bimorph_values
    } == valid_bimorph_values


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_set_channels_triggers_alltrgt_proc(
    mirror: BimorphMirror, valid_bimorph_values: dict[int, float], set_vout_mock
):
    mock_alltrgt_proc = get_mock_put(mirror.alltrgt_proc)

    mock_alltrgt_proc.assert_not_called()

    await mirror.set(valid_bimorph_values)

    mock_alltrgt_proc.assert_called_once()


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_set_channels_waits_for_vout_readback(
    mirror: BimorphMirror, valid_bimorph_values: dict[int, float], set_vout_mock
):
    with patch("dodal.devices.bimorph_mirror.wait_for_value") as mock_wait_for_value:
        mock_wait_for_value.assert_not_called()

        await mirror.set(valid_bimorph_values)

        assert [
            call(mirror.channels[i].vout, val, timeout=ANY)
            for i, val in valid_bimorph_values.items()
        ] == mock_wait_for_value.call_args_list


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_read(
    mirror: BimorphMirror, valid_bimorph_values: dict[int, float], set_vout_mock
):
    read = await mirror.read()

    assert [
        read[f"{mirror.name}-channels-{i}-vout"]["value"]
        for i in range(1, mirror.number_of_channels + 1)
    ] == list(valid_bimorph_values.values())


@pytest.mark.parametrize("mirror", VALID_BIMORPH_CHANNELS, indirect=True)
async def test_set_invalid_channel_throws_error(mirror: BimorphMirror):
    with pytest.raises(AssertionError):
        await mirror.set({mirror.number_of_channels + 1: 0.0})