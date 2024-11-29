import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, get_mock_put, set_mock_value

from dodal.devices.bimorph_mirror import BimorphMirror


@pytest.fixture
def mirror(RE: RunEngine) -> BimorphMirror:
    with DeviceCollector(mock=True):
        bm = BimorphMirror(prefix="BL02J-EA-IOC-97:G0:", number_of_channels=8)

    return bm


async def test_set_channels_waits_for_readback(mirror: BimorphMirror):
    value = {2: 50.0, 8: 24.0}

    set_mock_value(mirror.channels[2].vout, 50.0)
    set_mock_value(mirror.channels[8].vout, 24.0)
    await mirror.set(value)

    assert (await mirror.channels[2].vtrgt.get_value()) == 50.0
    assert (await mirror.channels[8].vtrgt.get_value()) == 24.0


async def test_set_channels_triggers_alltrgt_proc(mirror: BimorphMirror):
    value = {2: 50.0, 8: 24.0}

    mock_alltrgt_proc = get_mock_put(mirror.alltrgt_proc)

    set_mock_value(mirror.channels[2].vout, 50.0)
    set_mock_value(mirror.channels[8].vout, 24.0)

    mock_alltrgt_proc.assert_not_called()

    await mirror.set(value)

    mock_alltrgt_proc.assert_called_once()
