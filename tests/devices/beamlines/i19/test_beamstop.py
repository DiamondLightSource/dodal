import pytest
from daq_config_server.client import ConfigClient
from daq_config_server.testing import PathToMockDataDict

from dodal.common.enums import InOutUpper
from dodal.devices.beamlines.i19.beamstop import BeamStop

MOCK_BEAMLINE_PARAMS = "# Beamstop\nbeamstop_inbeam_x=5.0\nbeamstop_outbeam_x=3.37\n"


@pytest.fixture
def path_to_mock_data() -> PathToMockDataDict:
    return {"/path/to/params": MOCK_BEAMLINE_PARAMS}


@pytest.fixture
async def beamstop(mock_config_client: ConfigClient) -> BeamStop:
    beamstop = BeamStop("", "/path/to/params", mock_config_client, name="mock_beamstop")
    await beamstop.connect(mock=True)

    return beamstop


def test_beamstop_can_be_created(beamstop: BeamStop):
    assert isinstance(beamstop, BeamStop)


@pytest.mark.parametrize(
    "key, expected_value", [("beamstop_inbeam_x", 5.0), ("beamstop_outbeam_x", 3.37)]
)
def test_get_position_from_parameters_returns_correct_value(
    key: str, expected_value: float, beamstop: BeamStop
):
    position = beamstop._get_position_from_beamline_parameters(key)
    assert position == expected_value


@pytest.mark.parametrize(
    "move_request, expected_position", [(InOutUpper.IN, 5.0), (InOutUpper.OUT, 3.37)]
)
async def test_move_beamstop_to_position(
    move_request: InOutUpper, expected_position: float, beamstop: BeamStop
):
    await beamstop.set(move_request)

    assert await beamstop.x.user_readback.get_value() == expected_position
