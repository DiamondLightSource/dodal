import math
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Material:
    """
    Class representing a crystalline material with a specific lattice parameter.
    """

    name: str
    lattice_parameter: float


# Define known materials with their respective lattice parameters
KNOWN_MATERIALS = {
    "Si": Material(
        name="silicon", lattice_parameter=5.4310205e-10
    ),  # Silicon lattice parameter in meters
    "Ge": Material(
        name="germanium", lattice_parameter=5.6575e-10
    ),  # Germanium lattice parameter in meters
}


@dataclass(frozen=True)
class CrystalMetadata:
    """
    Metadata used in the NeXus format,
    see https://manual.nexusformat.org/classes/base_classes/NXcrystal.html
    """

    usage: Literal["Bragg", "Laue"] | None = None
    type: str | None = None
    reflection: tuple[int, int, int] | None = None
    d_spacing: tuple[float, str] | None = None

    def __init__(self, reflection_plane: str):
        # Determine material from reflection plane prefix
        material_prefix = reflection_plane[:2]
        if material_prefix not in KNOWN_MATERIALS:
            raise ValueError(
                f"Unsupported material: {material_prefix}. Only 'Si' and 'Ge' are supported."
            )

        material = KNOWN_MATERIALS[material_prefix]

        # Set attributes using object.__setattr__ since the class is frozen
        object.__setattr__(self, "type", material.name)
        reflection = self.parse_reflection_plane(reflection_plane)
        object.__setattr__(self, "reflection", reflection)
        d_spacing = self.calculate_d_spacing(material.lattice_parameter, reflection)
        object.__setattr__(self, "d_spacing", d_spacing)
        object.__setattr__(self, "usage", "Bragg")  # Assuming "Bragg" usage by default

    @staticmethod
    def parse_reflection_plane(plane: str) -> tuple[int, int, int]:
        """
        Parses a string like 'Si311' and returns the indices (h, k, l).
        """
        if len(plane) < 3 or not plane[2:].isdigit():
            raise ValueError(
                "Invalid reflection plane format. Expected format is 'TypeXYZ'."
            )
        indices = plane[2:]
        h, k, l = int(indices[0]), int(indices[1]), int(indices[2])
        return h, k, l

    @staticmethod
    def calculate_d_spacing(
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


# test with: python -m dodal.common.crystal_metadata
if __name__ == "__main__":
    # Example usage
    try:
        metadata_si311 = CrystalMetadata("Si311")
        print(metadata_si311)

        metadata_si111 = CrystalMetadata("Si111")
        print(metadata_si111)

        metadata_ge111 = CrystalMetadata("Ge111")
        print(metadata_ge111)

        # This will raise an error as 'Ga' (Gallium) is not supported
        metadata_ga111 = CrystalMetadata("Ga111")
    except ValueError as e:
        print(e)
