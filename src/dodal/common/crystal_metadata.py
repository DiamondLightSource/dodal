from dataclasses import dataclass
from enum import Enum
from typing import Literal


@dataclass(frozen=True)
class Material:
    """
    Class representing a crystalline material with a specific lattice parameter.
    """

    name: str
    lattice_parameter: float  # Lattice parameter in meters


class MaterialsEnum(Enum):
    Si = Material(name="silicon", lattice_parameter=5.4310205e-10)
    Ge = Material(name="germanium", lattice_parameter=5.6575e-10)


@dataclass(frozen=True)
class CrystalMetadata:
    """
    Metadata used in the NeXus format,
    see https://manual.nexusformat.org/classes/base_classes/NXcrystal.html
    """

    usage: Literal["Bragg", "Laue"] | None = None
    type: str | None = None
    reflection: tuple[int, int, int] | None = None

    def __init__(
        self,
        material: MaterialsEnum,
        reflection_plane: tuple[int, int, int],
        usage: str = "Bragg",
    ) -> None:
        # Determine material from reflection plane prefix
        # Set attributes using object.__setattr__ since the class is frozen
        assert all(
            i > 0 for i in reflection_plane
        ), "Reflection plane indices must be positive integers"
        object.__setattr__(self, "type", material.value.name)
        object.__setattr__(self, "reflection", reflection_plane)
        object.__setattr__(self, "usage", usage)
