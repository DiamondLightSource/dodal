import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, get_mock_put, set_mock_value

from dodal.devices.bimorph_mirror import BimorphMirror


@pytest.fixture
def mirror(RE: RunEngine) -> BimorphMirror:
    with DeviceCollector(mock=True):
        bm = BimorphMirror(prefix="BL02J-EA-IOC-97:G0:", number_of_channels=8)

    return bm


@pytest.mark.parametrize("value", [({2: 50.0, 8: 24.0})])
async def test_set_channels_waits_for_readback(
    value: dict[int, float], mirror: BimorphMirror
):
    for key, val in value.items():
        set_mock_value(mirror.channels[key].vout, val)

    await mirror.set(value)

    for key, val in value.items():
        assert (await mirror.channels[key].vtrgt.get_value()) == val


async def test_set_channels_triggers_alltrgt_proc(mirror: BimorphMirror):
    value = {2: 50.0, 8: 24.0}

    mock_alltrgt_proc = get_mock_put(mirror.alltrgt_proc)

    set_mock_value(mirror.channels[2].vout, 50.0)
    set_mock_value(mirror.channels[8].vout, 24.0)

    mock_alltrgt_proc.assert_not_called()

    await mirror.set(value)

    mock_alltrgt_proc.assert_called_once()
