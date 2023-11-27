from unittest.mock import MagicMock

import pytest
from ophyd.sim import instantiate_fake_device
from ophyd.status import Status

from dodal.devices.oav.oav_detector import OAV, OAVConfigParams
from dodal.devices.oav.oav_errors import (
    OAVError_BeamPositionNotFound,
    OAVError_ZoomLevelNotFound,
)

DISPLAY_CONFIGURATION = "tests/devices/unit_tests/test_display.configuration"
ZOOM_LEVELS_XML = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


@pytest.fixture
def oav() -> OAV:
    oav_params = OAVConfigParams(ZOOM_LEVELS_XML, DISPLAY_CONFIGURATION)
    oav: OAV = instantiate_fake_device(OAV, params=oav_params)
    oav.proc.port_name.sim_put("proc")
    oav.cam.port_name.sim_put("CAM")

    oav.zoom_controller.zrst.set("1.0x")
    oav.zoom_controller.onst.set("2.0x")
    oav.zoom_controller.twst.set("3.0x")
    oav.zoom_controller.thst.set("5.0x")
    oav.zoom_controller.frst.set("7.0x")
    oav.zoom_controller.fvst.set("9.0x")

    return oav


@pytest.mark.parametrize(
    "zoom, expected_plugin",
    [
        ("1.0x", "proc"),
        ("7.0x", "CAM"),
    ],
)
def test_when_zoom_level_changed_then_oav_rewired(zoom, expected_plugin, oav: OAV):
    oav.zoom_controller.set(zoom).wait()

    assert oav.mxsc.input_plugin.get() == expected_plugin
    assert oav.snapshot.input_plugin.get() == expected_plugin


def test_when_zoom_level_changed_then_status_waits_for_all_plugins_to_be_updated(
    oav: OAV,
):
    mxsc_status = Status()
    oav.mxsc.input_plugin.set = MagicMock(return_value=mxsc_status)

    mjpg_status = Status()
    oav.snapshot.input_plugin.set = MagicMock(return_value=mjpg_status)

    full_status = oav.zoom_controller.set("1.0x")

    assert mxsc_status in full_status
    assert mjpg_status in full_status


def test_load_microns_per_pixel_entry_not_found(oav: OAV):
    with pytest.raises(OAVError_ZoomLevelNotFound):
        oav.parameters.load_microns_per_pixel(0.000001)


@pytest.mark.parametrize(
    "zoom_level,expected_microns_x,expected_microns_y",
    [
        ("1.0x", 2.87, 2.87),
        ("2.5", 2.31, 2.31),
        ("5.0x", 1.58, 1.58),
        ("15.0", 0.302, 0.302),
    ],
)
def test_get_micronsperpixel_from_oav(
    zoom_level, expected_microns_x, expected_microns_y, oav: OAV
):
    oav.zoom_controller.level.sim_put(zoom_level)

    assert oav.parameters.micronsPerXPixel == expected_microns_x
    assert oav.parameters.micronsPerYPixel == expected_microns_y


def test_beam_position_not_found_for_wrong_entry(oav: OAV):
    with pytest.raises(OAVError_BeamPositionNotFound):
        oav.parameters.get_beam_position_from_zoom(2.0)


def test_get_beam_position(oav: OAV):
    expected_beam_position = (493, 355)
    beam_position = oav.parameters.get_beam_position_from_zoom(2.5)

    assert beam_position[0] == expected_beam_position[0]
    assert beam_position[1] == expected_beam_position[1]


@pytest.mark.parametrize(
    "zoom_level,expected_xCentre,expected_yCentre",
    [("1.0", 477, 359), ("5.0", 517, 350), ("10.0x", 613, 344)],
)
def test_extract_beam_position_given_different_zoom_levels(
    zoom_level,
    expected_xCentre,
    expected_yCentre,
    oav: OAV,
):
    oav.zoom_controller.level.sim_put(zoom_level)

    assert oav.parameters.beam_centre_i == expected_xCentre
    assert oav.parameters.beam_centre_j == expected_yCentre


@pytest.mark.parametrize(
    "h, v, expected_x, expected_y",
    [
        (54, 100, 517 - 54, 350 - 100),
        (0, 0, 517, 350),
        (500, 500, 517 - 500, 350 - 500),
    ],
)
def test_calculate_beam_distance(h, v, expected_x, expected_y, oav: OAV):
    oav.zoom_controller.level.sim_put("5.0x")

    assert oav.parameters.calculate_beam_distance(
        h,
        v,
    ) == (expected_x, expected_y)
