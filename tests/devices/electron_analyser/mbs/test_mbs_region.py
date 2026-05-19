from typing import Any

import pytest

from dodal.devices.beamlines.i05 import LensMode, PassEnergy
from dodal.devices.electron_analyser.base import EnergyMode
from dodal.devices.electron_analyser.mbs import AcquisitionMode, MbsRegion, MbsSequence
from dodal.devices.selectable_source import SelectedSource
from tests.devices.electron_analyser.helper_util import (
    assert_region_has_expected_values,
)
from tests.devices.electron_analyser.helper_util.sequence import (
    load_i05_mbs_test_xml_seq,
)


@pytest.fixture
def expected_xml_region_values() -> list[dict[str, Any]]:
    return [
        {
            "name": "mbs_region1",
            "enabled": True,
            "lens_mode": LensMode.L4_ANG0_D8,
            "pass_energy": PassEnergy.PE005,
            "slices": 1,
            "iterations": 3,
            "acquisition_mode": AcquisitionMode.SWEPT,
            "excitation_energy_source": SelectedSource.SOURCE1,
            "energy_mode": EnergyMode.KINETIC,
            "low_energy": 72.386,
            "high_energy": 73.814,
            "centre_energy": 73.1,
            "acquire_time": 1.0,
            "energy_step": 0.000405,
            "deflector_x": 0.0,
        },
    ]


def test_mbs_sequence_from_xml(
    expected_xml_region_values: list[dict[str, Any]],
) -> None:
    sequence = load_i05_mbs_test_xml_seq()
    for i, r in zip(sequence.regions, expected_xml_region_values, strict=True):
        assert_region_has_expected_values(i, r)


def test_mbs_region_load_using_field_names_has_expected_values(
    expected_xml_region_values: list[dict[str, Any]],
) -> None:
    for expected_region in expected_xml_region_values:
        r = MbsRegion[LensMode, PassEnergy].model_validate(expected_region)
        assert_region_has_expected_values(r, expected_region)

    seq = MbsSequence[LensMode, PassEnergy].model_validate(
        {"regions": expected_xml_region_values}
    )
    for r, expected_r in zip(seq.regions, expected_xml_region_values, strict=True):
        assert_region_has_expected_values(r, expected_r)
