import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine

from dodal.devices.oav.oav_detector import OAV, OAVConfigParams, ZoomController

TEST_GRID_TOP_LEFT_X = 100
TEST_GRID_TOP_LEFT_Y = 100
TEST_GRID_BOX_WIDTH = 25
TEST_GRID_NUM_BOXES_X = 5
TEST_GRID_NUM_BOXES_Y = 6


DISPLAY_CONFIGURATION = "tests/devices/unit_tests/test_display.configuration"
ZOOM_LEVELS_XML = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


def take_snapshot_with_grid(oav: OAV, snapshot_filename, snapshot_directory):
    oav.wait_for_connection()
    yield from bps.abs_set(oav.grid_snapshot.top_left_x, TEST_GRID_TOP_LEFT_X)  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
    yield from bps.abs_set(oav.grid_snapshot.top_left_y, TEST_GRID_TOP_LEFT_Y)  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
    yield from bps.abs_set(oav.grid_snapshot.box_width, TEST_GRID_BOX_WIDTH)  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
    yield from bps.abs_set(oav.grid_snapshot.num_boxes_x, TEST_GRID_NUM_BOXES_X)  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
    yield from bps.abs_set(oav.grid_snapshot.num_boxes_y, TEST_GRID_NUM_BOXES_Y)  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
    yield from bps.abs_set(oav.grid_snapshot.filename, snapshot_filename)  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
    yield from bps.abs_set(oav.grid_snapshot.directory, snapshot_directory)  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
    yield from bps.trigger(oav.grid_snapshot, wait=True)  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827


# We need to find a better way of integrating this, see https://github.com/DiamondLightSource/mx-bluesky/issues/183
@pytest.mark.skip(reason="Don't want to actually take snapshots during testing.")
def test_grid_overlay(RE: RunEngine):
    beamline = "BL03I"
    oav_params = OAVConfigParams(ZOOM_LEVELS_XML, DISPLAY_CONFIGURATION)
    oav = OAV(name="oav", prefix=f"{beamline}", params=oav_params)
    snapshot_filename = "snapshot"
    snapshot_directory = "."
    RE(take_snapshot_with_grid(oav, snapshot_filename, snapshot_directory))


@pytest.mark.skip(reason="No OAV in S03")
@pytest.mark.s03
def test_get_zoom_levels():
    my_zoom_controller = ZoomController("BL03S-EA-OAV-01:FZOOM:", name="test_zoom")
    my_zoom_controller.wait_for_connection()
    assert my_zoom_controller.allowed_zoom_levels[0] == "1.0x"
