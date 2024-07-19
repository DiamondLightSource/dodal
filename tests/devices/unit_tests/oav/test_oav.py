from unittest.mock import MagicMock

import pytest
from ophyd.sim import instantiate_fake_device
from ophyd.status import AndStatus, Status

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
    oav.proc.port_name.sim_put("proc")  # type: ignore
    oav.cam.port_name.sim_put("CAM")  # type: ignore

    oav.grid_snapshot.x_size.sim_put("1024")  # type: ignore
    oav.grid_snapshot.y_size.sim_put("768")  # type: ignore

    oav.zoom_controller.zrst.set("1.0x")
    oav.zoom_controller.onst.set("2.0x")
    oav.zoom_controller.twst.set("3.0x")
    oav.zoom_controller.thst.set("5.0x")
    oav.zoom_controller.frst.set("7.0x")
    oav.zoom_controller.fvst.set("9.0x")

    oav.wait_for_connection()

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

    assert oav.grid_snapshot.input_plugin.get() == expected_plugin


def test_when_zoom_level_changed_then_status_waits_for_all_plugins_to_be_updated(
    oav: OAV,
):
    mjpg_status = Status("mjpg - test_when_zoom_level...")
    oav.grid_snapshot.input_plugin.set = MagicMock(return_value=mjpg_status)

    assert isinstance(full_status := oav.zoom_controller.set("1.0x"), AndStatus)
    assert mjpg_status in full_status

    mjpg_status.set_finished()
    full_status.wait()


def test_load_microns_per_pixel_entry_not_found(oav: OAV):
    with pytest.raises(OAVError_ZoomLevelNotFound):
        oav.parameters.load_microns_per_pixel(0.000001, 0, 0)


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
    oav.zoom_controller.level.sim_put(zoom_level)  # type: ignore

    assert oav.parameters.micronsPerXPixel == pytest.approx(
        expected_microns_x, abs=1e-2
    )
    assert oav.parameters.micronsPerYPixel == pytest.approx(
        expected_microns_y, abs=1e-2
    )


def test_beam_position_not_found_for_wrong_entry(oav: OAV):
    with pytest.raises(OAVError_BeamPositionNotFound):
        oav.parameters.get_beam_position_from_zoom(2.0, 0, 0)


def test_get_beam_position(oav: OAV):
    expected_beam_position = (493, 355)
    beam_position = oav.parameters.get_beam_position_from_zoom(2.5, 1024, 768)

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
    oav.zoom_controller.level.sim_put(zoom_level)  # type: ignore

    assert oav.parameters.beam_centre_i == expected_xCentre
    assert oav.parameters.beam_centre_j == expected_yCentre


def test_extract_rescaled_micronsperpixel(oav: OAV):
    oav.grid_snapshot.x_size.sim_put("1292")  # type: ignore
    oav.grid_snapshot.y_size.sim_put("964")  # type: ignore
    oav.wait_for_connection()

    oav.zoom_controller.level.sim_put("1.0")  # type: ignore

    assert oav.parameters.micronsPerXPixel == pytest.approx(2.27, abs=1e-2)
    assert oav.parameters.micronsPerYPixel == pytest.approx(2.28, abs=1e-2)


def test_extract_rescaled_beam_position(oav: OAV):
    oav.grid_snapshot.x_size.sim_put("1292")  # type: ignore
    oav.grid_snapshot.y_size.sim_put("964")  # type: ignore
    oav.wait_for_connection()

    oav.zoom_controller.level.sim_put("1.0")  # type: ignore

    assert oav.parameters.beam_centre_i == 601
    assert oav.parameters.beam_centre_j == 450


@pytest.mark.parametrize(
    "h, v, expected_x, expected_y",
    [
        (54, 100, 517 - 54, 350 - 100),
        (0, 0, 517, 350),
        (500, 500, 517 - 500, 350 - 500),
    ],
)
def test_calculate_beam_distance(h, v, expected_x, expected_y, oav: OAV):
    oav.zoom_controller.level.sim_put("5.0x")  # type: ignore

    assert oav.parameters.calculate_beam_distance(
        h,
        v,
    ) == (expected_x, expected_y)


def test_when_oav_created_then_snapshot_parameters_set(oav: OAV):
    assert oav.snapshot.oav_params is not None
    assert oav.grid_snapshot.oav_params is not None
