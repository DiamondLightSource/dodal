from typing import Any

import pytest

from dodal.devices.beamlines.i05 import LensMode, PassEnergy
from dodal.devices.electron_analyser.base import EnergyMode
from dodal.devices.electron_analyser.mbs import AcquisitionMode, MbsSequence
from dodal.devices.selectable_source import SelectedSource
from tests.devices.electron_analyser.helper_util import (
    assert_region_has_expected_values,
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
            "energy_step": 0.405,
            "deflector_x": 0.0,
        },
    ]


def test_mbs_sequence_from_xml(
    expected_xml_region_values: list[dict[str, Any]],
) -> None:
    sequence = MbsSequence[LensMode, PassEnergy].from_xml(
        "tests/devices/electron_analyser/test_data/mbs_region1.arpes"
    )
    for i, r in zip(sequence.regions, expected_xml_region_values, strict=True):
        assert_region_has_expected_values(i, r)
