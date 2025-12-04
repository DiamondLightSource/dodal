from math import inf
from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import set_mock_value

from dodal.devices.aperturescatterguard import (
    ApertureScatterguard,
)
from dodal.devices.i04.beamsize import Beamsize
from dodal.devices.i04.transfocator import Transfocator


@pytest.mark.parametrize(
    "aperture_radius, transfocator_sizes, expected_beamsize",
    [
        (10.0, (50.0, 60.0), (10.0, 10.0)),
        (20.0, (10.0, 30.0), (10.0, 20.0)),
        (20.0, (30.0, 10.0), (20.0, 10.0)),
        (100.0, (50.0, 60.0), (50.0, 60.0)),
        (inf, (50.0, 60.0), (50.0, 60.0)),
    ],
)
async def test_beamsize_gives_min_of_aperture_and_transfocator_width_and_height(
    aperture_radius: float,
    transfocator_sizes: tuple[float, float],
    expected_beamsize: tuple[float, float],
    fake_transfocator: Transfocator,
    ap_sg: ApertureScatterguard,
):
    set_mock_value(ap_sg.aperture.medium, 1)

    ap_sg.radius.read = AsyncMock(
        return_value={
            "test_ap_sg-radius": {
                "value": aperture_radius,
                "timestamp": 1763051436.7372239,
                "alarm_severity": 0,
            }
        }
    )  # see https://github.com/bluesky/ophyd-async/issues/1132

    set_mock_value(fake_transfocator.current_horizontal_size_rbv, transfocator_sizes[0])
    set_mock_value(fake_transfocator.current_vertical_size_rbv, transfocator_sizes[1])

    beamsize = Beamsize(transfocator=fake_transfocator, aperture_scatterguard=ap_sg)

    beamsize_x = await beamsize.x_um.get_value()
    beamsize_y = await beamsize.y_um.get_value()
    assert (beamsize_x, beamsize_y) == expected_beamsize
