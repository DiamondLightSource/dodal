from dataclasses import dataclass

I03_BEAM_HEIGHT_UM = 20.0
I03_BEAM_WIDTH_UM = 80.0


@dataclass
class BeamSize:
    x_um: float | None
    y_um: float | None


def beam_size_from_aperture(aperture_size: float | None):
    return BeamSize(
        min(aperture_size, I03_BEAM_WIDTH_UM) if aperture_size else None,
        I03_BEAM_HEIGHT_UM if aperture_size else None,
    )
