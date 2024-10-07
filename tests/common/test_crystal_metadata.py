import pytest

from dodal.common.crystal_metadata import CrystalMetadata


def test_unsupported_material_value_error():
    with pytest.raises(
        ValueError, match="Unsupported material: Ga. Only 'Si' and 'Ge' are supported."
    ):
        CrystalMetadata(reflection_plane="Ga311")  # Unsupported "Ga" prefix


def test_invalid_reflection_plane_format_value_error():
    with pytest.raises(
        ValueError,
        match="Invalid reflection plane format. Expected format is 'TypeXYZ'.",
    ):
        CrystalMetadata(reflection_plane="Si31A")  # Invalid format


def test_happy_path_silicon():
    crystal_metadata = CrystalMetadata(reflection_plane="Si311")

    # Check the values
    assert crystal_metadata.type == "silicon"
    assert crystal_metadata.reflection == (3, 1, 1)
    assert crystal_metadata.d_spacing == pytest.approx(
        (0.16375, "nm"), rel=1e-3
    )  # Allow for small tolerance
    assert crystal_metadata.usage == "Bragg"


def test_happy_path_germanium():
    crystal_metadata = CrystalMetadata(reflection_plane="Ge111")

    # Check the values
    assert crystal_metadata.type == "germanium"
    assert crystal_metadata.reflection == (1, 1, 1)
    assert crystal_metadata.d_spacing == pytest.approx(
        (0.326633, "nm"), rel=1e-3
    )  # Allow for small tolerance
    assert crystal_metadata.usage == "Bragg"
