import pytest

from dodal.common.crystal_metadata import CrystalMetadata, MaterialsEnum


def test_happy_path_silicon():
    crystal_metadata = CrystalMetadata(
        material=MaterialsEnum.Si, reflection_plane=(3, 1, 1)
    )

    # Check the values
    assert crystal_metadata.type == "silicon"
    assert crystal_metadata.reflection == (3, 1, 1)
    assert crystal_metadata.d_spacing == pytest.approx(
        (0.16375, "nm"), rel=1e-3
    )  # Allow for small tolerance
    assert crystal_metadata.usage == "Bragg"


def test_happy_path_germanium():
    crystal_metadata = CrystalMetadata(
        material=MaterialsEnum.Ge, reflection_plane=(1, 1, 1)
    )

    # Check the values
    assert crystal_metadata.type == "germanium"
    assert crystal_metadata.reflection == (1, 1, 1)
    assert crystal_metadata.d_spacing == pytest.approx(
        (0.326633, "nm"), rel=1e-3
    )  # Allow for small tolerance
    assert crystal_metadata.usage == "Bragg"


def test_invalid_reflection_plane_with_negative_number():
    with pytest.raises(
        AssertionError,
        match="Reflection plane indices must be positive integers",
    ):
        CrystalMetadata(material=MaterialsEnum.Si, reflection_plane=(-1, 2, 3))
