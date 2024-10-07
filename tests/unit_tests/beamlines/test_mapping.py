import pytest

from dodal.beamlines import (
    all_beamline_names,
    module_name_for_beamline,
)


@pytest.mark.parametrize(
    "beamline,expected_module",
    {
        "i03": "i03",
        "s03": "i03",
        "i04-1": "i04_1",
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
    assert "i04-1" in beamlines


def test_all_beamline_names_includes_overriden_default_modules():
    beamlines = set(all_beamline_names())
    assert "i03" in beamlines
    assert "s03" in beamlines
