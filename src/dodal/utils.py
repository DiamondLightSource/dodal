from collections import namedtuple
from dataclasses import dataclass
from os import environ

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

    def __post_init__(self):
        if "i" in self.ixx.lower():
            suffix = "I"
        elif "b" in self.ixx.lower():
            suffix = "B"
        else:
            suffix = "S"
        self.beamline_prefix = f"BL{self.ixx[1:]}{suffix}"
        self.insertion_prefix = f"SR{self.ixx[1:]}{suffix}"
