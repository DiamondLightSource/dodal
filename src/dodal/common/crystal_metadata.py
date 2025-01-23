import math
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

    usage: Literal["Bragg", "Laue"]
    type: str
    reflection: tuple[int, int, int]
    d_spacing: tuple[float, str]

    @staticmethod
    def calculate_default_d_spacing(
        lattice_parameter: float, reflection: tuple[int, int, int]
    ) -> tuple[float, str]:
        """
        Calculates the d-spacing value in nanometers based on the given lattice parameter and reflection indices.
        """
        h_index, k_index, l_index = reflection
        d_spacing_m = lattice_parameter / math.sqrt(
            h_index**2 + k_index**2 + l_index**2
        )
        d_spacing_nm = d_spacing_m * 1e9  # Convert meters to nanometers
        return round(d_spacing_nm, 5), "nm"


def make_crystal_metadata_from_material(
    material: MaterialsEnum,
    reflection_plane: tuple[int, int, int],
    usage: Literal["Bragg", "Laue"] = "Bragg",
    d_spacing_param: tuple[float, str] | None = None,
):
    d_spacing = d_spacing_param or CrystalMetadata.calculate_default_d_spacing(
        material.value.lattice_parameter, reflection_plane
    )
    assert all(isinstance(i, int) and i > 0 for i in reflection_plane), (
        "Reflection plane indices must be positive integers"
    )
    return CrystalMetadata(usage, material.value.name, reflection_plane, d_spacing)
