import pytest

from dodal.beamline_specific_utils.i03 import (
    I03_BEAM_HEIGHT_UM,
    beam_size_from_aperture,
)

RADII_AND_SIZES = [
    (None, (None, None)),
    (123, (80, I03_BEAM_HEIGHT_UM)),
    (23.45, (23.45, I03_BEAM_HEIGHT_UM)),
    (50, (50, I03_BEAM_HEIGHT_UM)),
    (888, (80, I03_BEAM_HEIGHT_UM)),
]


@pytest.mark.parametrize(["aperture_radius", "beam_size"], RADII_AND_SIZES)
def test_beam_size_from_aperture(aperture_radius, beam_size):
    beamsize = beam_size_from_aperture(
        aperture_radius,
    )
    assert beamsize.x_um == beam_size[0]
    assert beamsize.y_um == beam_size[1]
