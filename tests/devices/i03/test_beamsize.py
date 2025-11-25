from math import inf
from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import set_mock_value

from dodal.devices.aperturescatterguard import (
    ApertureScatterguard,
)
from dodal.devices.i03.beamsize import Beamsize


@pytest.mark.parametrize(
    "aperture_radius, expected_beamsize",
    [
        (10.0, (10.0, 10.0)),
        (50, (50.0, 20.0)),
        (90, (80.0, 20.0)),
        (inf, (80.0, 20.0)),
    ],
)
async def test_beamsize_gives_min_of_aperture_and_beam_width_and_height(
    aperture_radius: float,
    expected_beamsize: tuple[float, float],
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

    beamsize = Beamsize(aperture_scatterguard=ap_sg)

    beamsize_x = await beamsize.x_um.get_value()
    beamsize_y = await beamsize.y_um.get_value()
    assert (beamsize_x, beamsize_y) == expected_beamsize
