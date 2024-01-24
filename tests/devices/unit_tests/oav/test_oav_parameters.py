import pytest

from dodal.devices.oav.oav_detector import OAVConfigParams
from dodal.devices.oav.oav_parameters import OAVParameters

OAV_CENTRING_JSON = "tests/devices/unit_tests/test_OAVCentring.json"
DISPLAY_CONFIGURATION = "tests/devices/unit_tests/test_display.configuration"
ZOOM_LEVELS_XML = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


@pytest.fixture
def mock_parameters():
    return OAVParameters(
        "loopCentring",
        OAV_CENTRING_JSON,
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


def test_given_context_and_microns_per_pixel_get_max_tip_distance_in_pixels(
    mock_parameters: OAVParameters,
):
    zoom_level = mock_parameters.zoom
    config_params = OAVConfigParams(ZOOM_LEVELS_XML, DISPLAY_CONFIGURATION)
    config_params.update_on_zoom(str(zoom_level), 1024, 768)

    assert mock_parameters.max_tip_distance == 300
    assert mock_parameters.get_max_tip_distance_in_pixels(
        config_params.micronsPerXPixel
    ) == pytest.approx(189.873, abs=1e-3)
