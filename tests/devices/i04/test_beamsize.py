import pytest
from ophyd_async.testing import set_mock_value

from dodal.devices.aperturescatterguard import (
    AperturePosition,
    ApertureScatterguard,
    ApertureValue,
)
from dodal.devices.i04.beamsize import Beamsize
from dodal.devices.i04.transfocator import Transfocator
from tests.devices.conftest import set_to_position


@pytest.mark.parametrize(
    "selected_aperture, aperture_signal_values, transfocator_sizes, expected_beamsize",
    [
        (ApertureValue.SMALL, (1, 0, 0), (10.0, 10.0), (10.0, 10.0)),
        (ApertureValue.SMALL, (1, 0, 0), (30.0, 10.0), (20.0, 10.0)),
        (ApertureValue.SMALL, (1, 0, 0), (10.0, 30.0), (10.0, 20.0)),
        (ApertureValue.SMALL, (1, 0, 0), (55.0, 30.0), (20.0, 20.0)),
        (ApertureValue.MEDIUM, (0, 1, 0), (10.0, 10.0), (10.0, 10.0)),
        (ApertureValue.MEDIUM, (0, 1, 0), (30.0, 70.0), (30.0, 50.0)),
        (ApertureValue.MEDIUM, (0, 1, 0), (70.0, 30.0), (50.0, 30.0)),
        (ApertureValue.MEDIUM, (0, 1, 0), (90.0, 90.0), (50.0, 50.0)),
        (ApertureValue.LARGE, (0, 0, 1), (90.0, 55.0), (90.0, 55.0)),
        (ApertureValue.LARGE, (0, 0, 1), (110.0, 55.0), (100.0, 55.0)),
        (ApertureValue.LARGE, (0, 0, 1), (90.0, 110.0), (90.0, 100.0)),
        (ApertureValue.LARGE, (0, 0, 1), (120.0, 120.0), (100.0, 100.0)),
        (ApertureValue.OUT_OF_BEAM, (0, 0, 0), (120.0, 10.0), (0.0, 0.0)),
        (ApertureValue.OUT_OF_BEAM, (0, 0, 0), (10.0, 120.0), (0.0, 0.0)),
        (ApertureValue.PARKED, (0, 0, 0), (10.0, 10.0), (0.0, 0.0)),
        (ApertureValue.PARKED, (0, 0, 0), (120.0, 120.0), (0.0, 0.0)),
    ],
)
async def test_beamsize_gives_min_of_aperture_and_transfocator_width_and_height(
    selected_aperture: ApertureValue,
    aperture_signal_values: tuple[int, int, int],
    transfocator_sizes: tuple[float, float],
    expected_beamsize: tuple[float, float],
    fake_transfocator: Transfocator,
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    await set_to_position(ap_sg, aperture_positions[selected_aperture])

    for i, signal in enumerate(
        (ap_sg.aperture.small, ap_sg.aperture.medium, ap_sg.aperture.large)
    ):
        set_mock_value(signal, aperture_signal_values[i])
    set_mock_value(fake_transfocator.current_horizontal_size_rbv, transfocator_sizes[0])
    set_mock_value(fake_transfocator.current_vertical_size_rbv, transfocator_sizes[1])

    beamsize = Beamsize(transfocator=fake_transfocator, aperture_scatterguard=ap_sg)

    beamsize_x = await beamsize.x_um.get_value()
    beamsize_y = await beamsize.y_um.get_value()
    assert (beamsize_x, beamsize_y) == expected_beamsize
