import random

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, get_mock_put, set_mock_value

from dodal.devices.bimorph_mirror import BimorphMirror

BIMORPH_NAME = "bimorph"
BIMORPH_NUMBER_OF_CHANNELS = 8


@pytest.fixture
def mirror(
    RE: RunEngine, number_of_channels=BIMORPH_NUMBER_OF_CHANNELS
) -> BimorphMirror:
    with DeviceCollector(mock=True):
        bm = BimorphMirror(
            name=BIMORPH_NAME,
            prefix="BL02J-EA-IOC-97:G0:",
            number_of_channels=number_of_channels,
        )

    return bm


@pytest.fixture
def valid_bimorph_values(number_of_channels: int) -> dict[int, float]:
    return {i: random.random() * 200 for i in range(1, number_of_channels + 1)}


@pytest.fixture
def set_vout_mock_and_return_value(request, mirror: BimorphMirror):
    for key, val in request.param.items():
        set_mock_value(mirror.channels[key].vout, val)

    return request.param


@pytest.mark.parametrize(
    "set_vout_mock_and_return_value", [({2: 50.0, 8: 24.0})], indirect=True
)
async def test_set_channels_waits_for_readback(
    set_vout_mock_and_return_value: dict[int, float], mirror: BimorphMirror
):
    value = set_vout_mock_and_return_value

    await mirror.set(value)

    for key, val in value.items():
        assert (await mirror.channels[key].vtrgt.get_value()) == val


@pytest.mark.parametrize(
    "set_vout_mock_and_return_value", [({2: 50.0, 8: 24.0})], indirect=True
)
async def test_set_channels_triggers_alltrgt_proc(
    set_vout_mock_and_return_value: dict[int, float], mirror: BimorphMirror
):
    value = set_vout_mock_and_return_value

    mock_alltrgt_proc = get_mock_put(mirror.alltrgt_proc)

    mock_alltrgt_proc.assert_not_called()

    await mirror.set(value)

    mock_alltrgt_proc.assert_called_once()


@pytest.mark.parametrize("value", [({2: 50.0, 8: 24.0})])
async def test_set_channels_waits_for_vout_readback(
    value: dict[int, float], mirror: BimorphMirror
):
    raise NotImplementedError


@pytest.mark.parametrize(
    "set_vout_mock_and_return_value",
    [({i: 0.0 for i in range(1, BIMORPH_NUMBER_OF_CHANNELS)})],
    indirect=True,
)
async def test_read(
    set_vout_mock_and_return_value: dict[int, float], mirror: BimorphMirror
):
    value = set_vout_mock_and_return_value

    read = await mirror.read()

    for i in range(1, mirror.number_of_channels):
        assert read[f"{BIMORPH_NAME}-channels-{i}-vout"]["value"] == value[i]
