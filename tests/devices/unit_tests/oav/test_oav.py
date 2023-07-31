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
    assert oav.snapshot.input_plugin.get() == "OAV.MXSC"


def test_when_zoom_level_changed_then_status_waits_for_all_plugins_to_be_updated(
    oav: OAV,
):
    expected_exception = Exception()
    plugin_status = Status()
    # We're using an exception as a proxy to tell that we're waiting on this set too
    plugin_status.set_exception(expected_exception)
    oav.mxsc.input_plugin.set = MagicMock(return_value=plugin_status)

    full_status = oav.zoom_controller.set("1.0x")

    assert full_status.exception == expected_exception
