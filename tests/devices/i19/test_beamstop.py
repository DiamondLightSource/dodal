import pytest

from dodal.devices.i19.beamstop import BeamStop


@pytest.fixture
async def beamstop() -> BeamStop:
    beamstop = BeamStop("", "mock_beamstop")
    await beamstop.connect(mock=True)

    return beamstop


def test_beamstop_can_be_created(beamstop: BeamStop):
    assert isinstance(beamstop, BeamStop)
