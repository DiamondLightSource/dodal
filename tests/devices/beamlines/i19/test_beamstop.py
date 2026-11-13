import pytest
from daq_config_server.client import ConfigClient
from daq_config_server.testing import PathToMockDataDict

from dodal.common.enums import InOutUpper
from dodal.devices.beamlines.i19.beamstop import BeamStop, HutchState

MOCK_BEAMLINE_PARAMS = """
# Beamstop
beamstop_inbeam_x=5.0
beamstop_outbeam_x=3.37
beamstop_inbeam_y=1.32
beamstop_outbeam_y=-44.0
"""


@pytest.fixture
def path_to_mock_data() -> PathToMockDataDict:
    return {"/path/to/params": MOCK_BEAMLINE_PARAMS}


@pytest.fixture
async def beamstop_eh1(mock_config_client: ConfigClient) -> BeamStop:
    beamstop = BeamStop(
        "", HutchState.EH1, "/path/to/params", mock_config_client, name="mock_beamstop"
    )
    await beamstop.connect(mock=True)

    return beamstop


@pytest.fixture
async def beamstop_eh2(mock_config_client: ConfigClient) -> BeamStop:
    beamstop = BeamStop(
        "", HutchState.EH2, "/path/to/params", mock_config_client, name="mock_beamstop"
    )
    await beamstop.connect(mock=True)

    return beamstop


def test_beamstop_can_be_created(beamstop_eh2: BeamStop):
    assert isinstance(beamstop_eh2, BeamStop)


@pytest.mark.parametrize(
    "key, expected_value", [("beamstop_inbeam_y", 1.32), ("beamstop_outbeam_y", -44.0)]
)
def test_get_position_from_parameters_returns_correct_value_for_eh1(
    key: str, expected_value: float, beamstop_eh1: BeamStop
):
    position = beamstop_eh1._get_position_from_beamline_parameters(key)
    assert position == expected_value


@pytest.mark.parametrize(
    "key, expected_value", [("beamstop_inbeam_x", 5.0), ("beamstop_outbeam_x", 3.37)]
)
def test_get_position_from_parameters_returns_correct_value_for_eh2(
    key: str, expected_value: float, beamstop_eh2: BeamStop
):
    position = beamstop_eh2._get_position_from_beamline_parameters(key)
    assert position == expected_value


@pytest.mark.parametrize(
    "move_request, expected_position",
    [
        (InOutUpper.IN, 1.32),
        (InOutUpper.OUT, -44),
    ],
)
async def test_move_beamstop_y_to_position_for_eh2(
    move_request: InOutUpper,
    expected_position: float,
    beamstop_eh1: BeamStop,
):
    await beamstop_eh1.set(move_request)

    assert await beamstop_eh1.y.user_readback.get_value() == expected_position


@pytest.mark.parametrize(
    "move_request, expected_position",
    [
        (InOutUpper.IN, 5.0),
        (InOutUpper.OUT, 3.37),
    ],
)
async def test_move_beamstop_x_to_position_for_eh2(
    move_request: InOutUpper,
    expected_position: float,
    beamstop_eh2: BeamStop,
):
    await beamstop_eh2.set(move_request)

    assert await beamstop_eh2.x.user_readback.get_value() == expected_position
