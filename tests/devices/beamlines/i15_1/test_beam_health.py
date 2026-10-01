import pytest
from ophyd_async.core import init_devices, set_mock_value

from dodal.devices.beamlines.i15_1.beam_health import BeamHealth


@pytest.fixture
async def beam_health():
    with init_devices(mock=True):
        beam_health = BeamHealth("")
    return beam_health


@pytest.mark.parametrize("pv_value, expected_healthy", [(0.0, False), (1.0, True)])
async def test_beam_healthy_read_as_bool(
    pv_value: float, expected_healthy: bool, beam_health: BeamHealth
):
    set_mock_value(beam_health._healthy_float, pv_value)
    assert await beam_health.healthy.get_value() is expected_healthy
