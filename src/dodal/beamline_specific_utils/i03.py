from dataclasses import dataclass

from dodal.devices.aperturescatterguard import SingleAperturePosition

I03_BEAM_HEIGHT_UM = 20


@dataclass
class BeamSize:
    x_um: float | None
    y_um: float | None


def beam_size_from_aperture(position: SingleAperturePosition):
    aperture_size = position.radius_microns
    return BeamSize(aperture_size, I03_BEAM_HEIGHT_UM if aperture_size else None)
