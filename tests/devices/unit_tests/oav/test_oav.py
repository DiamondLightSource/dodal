from unittest.mock import MagicMock

import pytest
from ophyd.sim import instantiate_fake_device
from ophyd.status import Status

from dodal.devices.oav.oav_detector import OAV, OAVParams

DISPLAY_CONFIGURATION = "tests/devices/unit_tests/test_display.configuration"
ZOOM_LEVELS_XML = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


@pytest.fixture
def oav() -> OAV:
    oav_params = OAVParams(ZOOM_LEVELS_XML, DISPLAY_CONFIGURATION)
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


def test_get_micronsperpixel_from_oav(oav: OAV):
    oav.zoom_controller.level.sim_put("1.0x")
    # Update call failing with
    # File
    # "/scratch/uhz96441/workspaces/dodal/.venv/lib/python3.11/site-packages/ophyd/ophydobj.py",
    # line 492, in inner
    #   cb(*args, **kwargs)
    # TypeError: OAVParams.update_on_zoom() missing 1 required positional argument: 'zoom_level'
    print(oav.zoom_controller.level.get())

    # print(oav.parameters.update_on_zoom(zoom_level=oav.zoom_controller.level))
    assert oav.parameters.micronsPerXPixel == 2.87
