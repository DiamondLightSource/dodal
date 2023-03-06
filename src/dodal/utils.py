from collections import namedtuple
from dataclasses import dataclass
from os import environ
from typing import Optional

Point2D = namedtuple("Point2D", ["x", "y"])
Point3D = namedtuple("Point3D", ["x", "y", "z"])


def get_beamline_name(ixx: str) -> str:
    bl = environ.get("BEAMLINE")
    if bl is None:
        return f"s{ixx[1:]}"
    else:
        return bl


@dataclass
class BeamlinePrefix:
    ixx: str
    suffix: Optional[str] = None

    def __post_init__(self):
        self.suffix = self.ixx[0].upper() if not self.suffix else self.suffix
        self.beamline_prefix = f"BL{self.ixx[1:3]}{self.suffix}"
        self.insertion_prefix = f"SR{self.ixx[1:3]}{self.suffix}"
