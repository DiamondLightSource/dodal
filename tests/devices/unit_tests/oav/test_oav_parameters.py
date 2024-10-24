import pytest

from dodal.devices.oav.oav_parameters import (
    OAVConfig,
    OAVParameters,
    ZoomParams,
)

OAV_CENTRING_JSON = "tests/devices/unit_tests/test_OAVCentring.json"
DISPLAY_CONFIGURATION = "tests/devices/unit_tests/test_display.configuration"
ZOOM_LEVELS_XML = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


@pytest.fixture
def mock_parameters():
    return OAVParameters(
        "loopCentring",
        OAV_CENTRING_JSON,
    )


@pytest.fixture
def mock_config() -> dict[str, ZoomParams]:
    return OAVConfig(ZOOM_LEVELS_XML, DISPLAY_CONFIGURATION).get_parameters()


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
    "zoom_level, expected_microns, expected_crosshair",
    [
        ("2.5", (2.31, 2.31), (493, 355)),
        ("10.0", (0.438, 0.438), (613, 344)),
    ],
)
def test_oav_config(
    zoom_level, expected_microns, expected_crosshair, mock_config: dict
):
    assert isinstance(mock_config[zoom_level], ZoomParams)

    assert mock_config[zoom_level].crosshair == expected_crosshair
    assert mock_config[zoom_level].microns_per_pixel == expected_microns


def test_given_oav_config_get_max_tip_distance_in_pixels(
    mock_parameters: OAVParameters, mock_config: dict
):
    zoom_level = mock_parameters.zoom

    assert mock_parameters.max_tip_distance == 300
    microns_per_pixel_x = mock_config[str(zoom_level)].microns_per_pixel[0]
    assert microns_per_pixel_x
    assert mock_parameters.get_max_tip_distance_in_pixels(
        microns_per_pixel_x
    ) == pytest.approx(189.873, abs=1e-3)


def test_given_new_context_parameters_are_updated(mock_parameters: OAVParameters):
    mock_parameters.update_context("xrayCentring")

    assert mock_parameters.active_params.get("zoom") == 7.5
    assert mock_parameters.active_params.get("brightness") == 80
