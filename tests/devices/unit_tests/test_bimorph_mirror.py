import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, get_mock_put, set_mock_value

from dodal.devices.bimorph_mirror import BimorphMirror


@pytest.fixture
def mirror(RE: RunEngine) -> BimorphMirror:
    with DeviceCollector(mock=True):
        bm = BimorphMirror(prefix="BL02J-EA-IOC-97:G0:", number_of_channels=8)

    return bm


@pytest.fixture
def set_vout_mock_values(request, mirror: BimorphMirror):
    for key, val in request.param.items():
        set_mock_value(mirror.channels[key].vout, val)

    return request.param


@pytest.mark.parametrize("set_vout_mock_values", [({2: 50.0, 8: 24.0})], indirect=True)
async def test_set_channels_waits_for_readback(
    set_vout_mock_values: dict[int, float], mirror: BimorphMirror
):
    value = set_vout_mock_values

    await mirror.set(value)

    for key, val in value.items():
        assert (await mirror.channels[key].vtrgt.get_value()) == val


@pytest.mark.parametrize("set_vout_mock_values", [({2: 50.0, 8: 24.0})], indirect=True)
async def test_set_channels_triggers_alltrgt_proc(
    set_vout_mock_values: dict[int, float], mirror: BimorphMirror
):
    value = set_vout_mock_values

    mock_alltrgt_proc = get_mock_put(mirror.alltrgt_proc)

    mock_alltrgt_proc.assert_not_called()

    await mirror.set(value)

    mock_alltrgt_proc.assert_called_once()
