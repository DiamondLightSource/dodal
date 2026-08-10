from dataclasses import dataclass


@dataclass(frozen=True)
class BeamsizeConstants:
    BEAM_WIDTH_UM = 80.0
    BEAM_HEIGHT_UM = 20.0
