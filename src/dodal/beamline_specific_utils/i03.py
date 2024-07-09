from dataclasses import dataclass

from dodal.devices.aperturescatterguard import SingleAperturePosition

I03_BEAM_HEIGHT_UM = 20


@dataclass
class BeamSize:
    x_mm: float | None
    y_mm: float | None


def beam_size_from_aperture(position: SingleAperturePosition):
    aperture_size = position.radius_microns
    return (
        BeamSize(aperture_size / 1000, I03_BEAM_HEIGHT_UM / 1000)
        if aperture_size
        else BeamSize(None, None)
    )
