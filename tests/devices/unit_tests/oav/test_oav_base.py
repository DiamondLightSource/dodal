import pytest
from ophyd_async.testing import set_mock_value

from dodal.devices.oav.oav_detector_base import OAVBase


async def test_defaults_to_no_zoom(base_oav: OAVBase):
    assert await base_oav.zoom_level.get_value() == "1.0"


async def test_base_oav_returns_beam_position_and_microns_per_pixel_correctly(
    base_oav: OAVBase,
):
    set_mock_value(base_oav.grid_snapshot.x_size, 2012)
    set_mock_value(base_oav.grid_snapshot.y_size, 1518)

    microns_x = await base_oav.microns_per_pixel_x.get_value()
    microns_y = await base_oav.microns_per_pixel_y.get_value()
    beam_x = await base_oav.beam_centre_i.get_value()
    beam_y = await base_oav.beam_centre_j.get_value()

    assert microns_x == pytest.approx(1.46, abs=1e-2)
    assert microns_y == pytest.approx(1.45, abs=1e-2)
    assert beam_x == 937
    assert beam_y == 709
