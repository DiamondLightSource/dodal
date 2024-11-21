import pytest
from ophyd_async.core import get_mock

from dodal.devices.aithre_lasershaping.goniometer import Goniometer


async def test_stage_x_y():
    stages = Goniometer(prefix="LA18L-MO-LSR-01:")
    await stages.connect(mock=True)
    await stages.x.velocity.set(5)
    mock_velocity = get_mock(stages.x.velocity)
    mock_velocity.put.assert_called_once()


@pytest.mark.s03
async def test_stage_setup():
    # This needs to be run on a machine with access to the PVs!

    stages = Goniometer(prefix="LA18L-MO-LSR-01:")
    await stages.connect()

    # Set grid/beam position/scale.
    line_width = 2
    line_spacing = 115  # depends on pixel size, 60 for MANTA507B
    line_color = (140, 140, 140)  # greyness
    beamX = 2288
    beamY = 1310
    feed_width = await stages.x.high_limit_travel.get_value()
    assert feed_width > 0
    display_width = 2012
    display_height = 1518
    camera_pixel_size = 1.85  # Alvium1240M
    feed_display_ratio = feed_width / display_width
    calibrate = (
        camera_pixel_size / feed_display_ratio
    ) / 1000  # play around with the end number to find correct
