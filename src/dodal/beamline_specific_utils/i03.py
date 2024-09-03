from dataclasses import dataclass

from dodal.devices.aperturescatterguard import ApertureValue

I03_BEAM_HEIGHT_UM = 20


@dataclass
class BeamSize:
    x_um: float | None
    y_um: float | None


def beam_size_from_aperture(position: ApertureValue):
    aperture_size = position.radius
    return BeamSize(aperture_size, I03_BEAM_HEIGHT_UM if aperture_size else None)
