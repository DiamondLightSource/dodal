import pytest
from ophyd_async.core import DeviceCollector, set_mock_value

from dodal.devices.oav.oav_async import OAV, ZoomController
from dodal.devices.oav.oav_parameters import OAVConfig

DISPLAY_CONFIGURATION = "tests/devices/unit_tests/test_display.configuration"
ZOOM_LEVELS_XML = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


@pytest.fixture
async def oav() -> OAV:
    oav_config = OAVConfig(ZOOM_LEVELS_XML, DISPLAY_CONFIGURATION)
    async with DeviceCollector(mock=True, connect=True):
        oav = OAV("", config=oav_config, name="fake_oav")
    set_mock_value(oav.grid_snapshot.x_size, 1024)
    set_mock_value(oav.grid_snapshot.y_size, 768)
    return oav


async def test_zoom_controller():
    zoom_controller = ZoomController("", "fake zoom controller")
    await zoom_controller.connect(mock=True)
    status = zoom_controller.set("3.0x")
    await status
    assert status.success
    assert await zoom_controller.level.get_value() == "3.0x"


@pytest.mark.parametrize(
    "zoom_level,expected_microns_x,expected_microns_y",
    [
        ("1.0x", 2.87, 2.87),
        ("2.5", 2.31, 2.31),
        ("5.0x", 1.58, 1.58),
        ("15.0", 0.302, 0.302),
    ],
)
async def test_get_micronsperpixel_from_oav(
    zoom_level, expected_microns_x, expected_microns_y, oav: OAV
):
    set_mock_value(oav.zoom_controller.level, zoom_level)

    assert await oav.microns_per_pixel_x.get_value() == pytest.approx(
        expected_microns_x, abs=1e-2
    )
    assert await oav.microns_per_pixel_y.get_value() == pytest.approx(
        expected_microns_y, abs=1e-2
    )


@pytest.mark.parametrize(
    "zoom_level,expected_xCentre,expected_yCentre",
    [("1.0", 477, 359), ("5.0", 517, 350), ("10.0x", 613, 344)],
)
async def test_extract_beam_position_given_different_zoom_levels(
    zoom_level,
    expected_xCentre,
    expected_yCentre,
    oav: OAV,
):
    set_mock_value(oav.zoom_controller.level, zoom_level)

    assert await oav.beam_centre_i.get_value() == expected_xCentre
    assert await oav.beam_centre_j.get_value() == expected_yCentre


async def test_oav_returns_rescaled_beam_position_and_microns_per_pixel_correctly(
    oav: OAV,
):
    set_mock_value(oav.grid_snapshot.x_size, 1292)
    set_mock_value(oav.grid_snapshot.y_size, 964)

    set_mock_value(oav.zoom_controller.level, "1.0")

    microns_x = await oav.microns_per_pixel_x.get_value()
    microns_y = await oav.microns_per_pixel_y.get_value()
    beam_x = await oav.beam_centre_i.get_value()
    beam_y = await oav.beam_centre_j.get_value()

    assert microns_x == pytest.approx(2.27, abs=1e-2)
    assert microns_y == pytest.approx(2.28, abs=1e-2)
    assert beam_x == 601
    assert beam_y == 450


@pytest.mark.parametrize(
    "h, v, expected_x, expected_y",
    [
        (54, 100, 517 - 54, 350 - 100),
        (0, 0, 517, 350),
        (500, 500, 517 - 500, 350 - 500),
    ],
)
async def test_calculate_beam_distance(h, v, expected_x, expected_y, oav: OAV):
    set_mock_value(oav.zoom_controller.level, "5.0x")  # type: ignore

    assert await oav.calculate_beam_distance(
        h,
        v,
    ) == (expected_x, expected_y)


async def test_when_oav_created_microns_and_beam_centre_set_in_snapshots(oav: OAV):
    pass
