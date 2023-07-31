from unittest.mock import MagicMock

import pytest
from ophyd.sim import instantiate_fake_device
from ophyd.status import Status

from dodal.devices.oav.oav_detector import OAV


@pytest.fixture
def oav() -> OAV:
    oav: OAV = instantiate_fake_device(OAV)
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
