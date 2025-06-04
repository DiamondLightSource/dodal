from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.oav.oav_detector import OAVBeamCentreFile, OAVBeamCentrePV
from dodal.devices.oav.oav_parameters import OAVConfig, OAVConfigBeamCentre

DISPLAY_CONFIGURATION = "tests/devices/unit_tests/test_display.configuration"
ZOOM_LEVELS_XML = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


@pytest.fixture
async def oav() -> OAVBeamCentreFile:
    oav_config = OAVConfigBeamCentre(ZOOM_LEVELS_XML, DISPLAY_CONFIGURATION)
    async with init_devices(mock=True, connect=True):
        oav = OAVBeamCentreFile("", config=oav_config, name="oav")
    zoom_levels_list = ["1.0x", "3.0x", "5.0x", "7.5x", "10.0x"]
    oav.zoom_controller.level.describe = AsyncMock(
        return_value={"level": {"choices": zoom_levels_list}}
    )
    set_mock_value(oav.grid_snapshot.x_size, 1024)
    set_mock_value(oav.grid_snapshot.y_size, 768)
    set_mock_value(oav.zoom_controller.level, "1.0x")
    return oav


@pytest.fixture
async def oav_beam_centre_pv_roi() -> OAVBeamCentrePV:
    oav_config = OAVConfig(ZOOM_LEVELS_XML)
    async with init_devices(mock=True, connect=True):
        oav = OAVBeamCentrePV("", config=oav_config, name="oav")
    zoom_levels_list = ["1.0x", "3.0x", "5.0x", "7.5x", "10.0x"]
    oav.zoom_controller.level.describe = AsyncMock(
        return_value={"level": {"choices": zoom_levels_list}}
    )
    set_mock_value(oav.grid_snapshot.x_size, 1024)
    set_mock_value(oav.grid_snapshot.y_size, 768)
    set_mock_value(oav.zoom_controller.level, "1.0x")
    return oav


@pytest.fixture
async def oav_beam_centre_pv_fs() -> OAVBeamCentrePV:
    oav_config = OAVConfig(ZOOM_LEVELS_XML)
    async with init_devices(mock=True, connect=True):
        oav = OAVBeamCentrePV("", config=oav_config, name="oav", overlay_channel=3)
    zoom_levels_list = ["1.0x", "3.0x", "5.0x", "7.5x", "10.0x"]
    oav.zoom_controller.level.describe = AsyncMock(
        return_value={"level": {"choices": zoom_levels_list}}
    )
    set_mock_value(oav.grid_snapshot.x_size, 1024)
    set_mock_value(oav.grid_snapshot.y_size, 768)
    set_mock_value(oav.zoom_controller.level, "1.0x")
    return oav
