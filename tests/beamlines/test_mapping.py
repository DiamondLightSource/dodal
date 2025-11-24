import pytest

from dodal.beamlines import (
    all_beamline_names,
    module_name_for_beamline,
)


@pytest.mark.parametrize(
    "beamline,expected_module",
    {
        "i03": "i03",
        "i20-1": "i20_1",
        "i22": "i22",
    }.items(),
)
def test_beamline_name_mapping(beamline: str, expected_module: str):
    assert module_name_for_beamline(beamline) == expected_module


def test_all_beamline_names_includes_non_overridden_modules():
    beamlines = set(all_beamline_names())
    assert "i22" in beamlines


def test_all_beamline_names_includes_overriden_modules():
    beamlines = set(all_beamline_names())
    assert "i20-1" in beamlines
    assert "i19-2" in beamlines


def test_all_beamline_names_includes_overriden_default_modules():
    beamlines = set(all_beamline_names())
    assert "i03" in beamlines
