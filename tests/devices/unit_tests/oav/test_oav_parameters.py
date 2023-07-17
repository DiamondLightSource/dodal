import pytest

from dodal.devices.oav.oav_errors import OAVError_ZoomLevelNotFound
from dodal.devices.oav.oav_parameters import OAVParameters

OAV_CENTRING_JSON = "tests/devices/unit_tests/test_OAVCentring.json"
DISPLAY_CONFIGURATION = "tests/devices/unit_tests/test_display.configuration"
ZOOM_LEVELS_XML = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


@pytest.fixture
def mock_parameters():
    return OAVParameters(
        "loopCentring", ZOOM_LEVELS_XML, OAV_CENTRING_JSON, DISPLAY_CONFIGURATION
    )


def test_given_key_in_context_but_not_default_when_load_parameters_then_value_found(
    mock_parameters: OAVParameters,
):
    assert mock_parameters.zoom == 5.0


def test_given_key_in_default_but_not_context_when_load_parameters_then_value_found(
    mock_parameters: OAVParameters,
):
    assert mock_parameters.gain == 1.0


def test_given_key_in_context_and_default_when_load_parameters_then_value_found_from_context(
    mock_parameters: OAVParameters,
):
    assert mock_parameters.minimum_height == 10


@pytest.mark.parametrize(
    "zoom_level,expected_xCentre,expected_yCentre",
    [(1.0, 477, 359), (5.0, 517, 350), (10.0, 613, 344)],
)
def test_extract_beam_position_different_beam_postitions(
    zoom_level,
    expected_xCentre,
    expected_yCentre,
    mock_parameters: OAVParameters,
):
    mock_parameters.zoom = zoom_level
    mock_parameters._extract_beam_position()
    assert mock_parameters.beam_centre_i == expected_xCentre
    assert mock_parameters.beam_centre_j == expected_yCentre


@pytest.mark.parametrize(
    "zoom_level,expected_microns_x,expected_microns_y",
    [(2.5, 2.31, 2.31), (15.0, 0.302, 0.302)],
)
def test_load_microns_per_pixel_entries_found(
    zoom_level, expected_microns_x, expected_microns_y, mock_parameters: OAVParameters
):
    mock_parameters.load_microns_per_pixel(zoom_level)
    assert mock_parameters.micronsPerXPixel == expected_microns_x
    assert mock_parameters.micronsPerYPixel == expected_microns_y


def test_load_microns_per_pixel_entry_not_found(mock_parameters: OAVParameters):
    with pytest.raises(OAVError_ZoomLevelNotFound):
        mock_parameters.load_microns_per_pixel(0.000001)


@pytest.mark.parametrize(
    "h, v, expected_x, expected_y",
    [
        (54, 100, 517 - 54, 350 - 100),
        (0, 0, 517, 350),
        (500, 500, 517 - 500, 350 - 500),
    ],
)
def test_calculate_beam_distance(
    h, v, expected_x, expected_y, mock_parameters: OAVParameters
):
    assert mock_parameters.calculate_beam_distance(
        h,
        v,
    ) == (expected_x, expected_y)
