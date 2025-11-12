import pytest
from ophyd_async.testing import set_mock_value

from dodal.devices.aperturescatterguard import (
    AperturePosition,
    ApertureScatterguard,
    ApertureValue,
)
from dodal.devices.i03.beamsize import Beamsize
from tests.devices.conftest import set_to_position


@pytest.mark.parametrize(
    "selected_aperture, aperture_signal_values, expected_beamsize",
    [
        (ApertureValue.SMALL, (1, 0, 0), (20.0, 20.0)),
        (ApertureValue.MEDIUM, (0, 1, 0), (50.0, 20.0)),
        (ApertureValue.LARGE, (0, 0, 1), (80.0, 20.0)),
        (ApertureValue.OUT_OF_BEAM, (0, 0, 0), (0.0, 0.0)),
        (ApertureValue.PARKED, (0, 0, 0), (0.0, 0.0)),
    ],
)
async def test_beamsize_gives_min_of_aperture_and_beam_width_and_height(
    selected_aperture: ApertureValue,
    aperture_signal_values: tuple[int, int, int],
    expected_beamsize: tuple[float, float],
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    await set_to_position(ap_sg, aperture_positions[selected_aperture])

    for i, signal in enumerate(
        (ap_sg.aperture.small, ap_sg.aperture.medium, ap_sg.aperture.large)
    ):
        set_mock_value(signal, aperture_signal_values[i])

    beamsize = Beamsize(aperture_scatterguard=ap_sg)
    beamsize_x = await beamsize.x_um.get_value()
    beamsize_y = await beamsize.y_um.get_value()
    assert beamsize_x == expected_beamsize[0]
    assert beamsize_y == expected_beamsize[1]
