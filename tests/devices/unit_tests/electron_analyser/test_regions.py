from abc import ABC, abstractmethod
from typing import Any, Generic

import pytest

from dodal.devices.electron_analyser.abstract_region import (
    EnergyMode,
    TAbstractBaseRegion,
    TAbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs_region import SpecsRegion, SpecsSequence
from dodal.devices.electron_analyser.vgscienta_region import (
    AcquisitionMode,
    DetectorMode,
    Status,
    VGScientaRegion,
    VGScientaSequence,
)


class TestAbstractSequenceAndRegions(
    ABC, Generic[TAbstractBaseSequence, TAbstractBaseRegion]
):
    @pytest.fixture
    @abstractmethod
    def sequence_file(self) -> str:
        pass

    @pytest.fixture
    @abstractmethod
    def sequence_class(self) -> type[TAbstractBaseSequence]:
        pass

    @pytest.fixture
    @abstractmethod
    def expected_region_class(self) -> type[TAbstractBaseRegion]:
        pass

    @pytest.fixture
    @abstractmethod
    def expected_region_values(self) -> list[dict[str, Any]]:
        pass

    @pytest.fixture
    def expected_region_names(
        self,
        expected_region_values: list[dict[str, Any]],
    ) -> list[str]:
        names = []
        for expected_region_value in expected_region_values:
            names.append(expected_region_value["name"])
        return names

    @pytest.fixture
    def expected_enabled_region_names(
        self,
        expected_region_values: list[dict[str, Any]],
    ) -> list[str]:
        names = []
        for expected_region_value in expected_region_values:
            if expected_region_value["enabled"]:
                names.append(expected_region_value["name"])
        return names

    def test_get_expected_region_from_name(
        self, sequence: TAbstractBaseSequence, expected_region_names: list[str]
    ) -> None:
        for name in expected_region_names:
            assert sequence.get_region_by_name(name) is not None
        assert (
            sequence.get_region_by_name("region name should not be in sequence") is None
        )

    def test_sequence_get_expected_region_type(
        self,
        sequence: TAbstractBaseSequence,
        expected_region_class: type[TAbstractBaseRegion],
    ) -> None:
        regions = sequence.regions
        enabled_regions = sequence.get_enabled_regions()
        assert isinstance(regions, list) and all(
            isinstance(r, expected_region_class) for r in regions
        )
        assert isinstance(enabled_regions, list) and all(
            isinstance(r, expected_region_class) for r in enabled_regions
        )

    def test_sequence_get_expected_region_names(
        self, sequence: TAbstractBaseSequence, expected_region_names: list[str]
    ) -> None:
        assert sequence.get_region_names() == expected_region_names

    def test_sequence_get_expected_enabled_region_names(
        self, sequence: TAbstractBaseSequence, expected_enabled_region_names: list[str]
    ) -> None:
        assert sequence.get_enabled_region_names() == expected_enabled_region_names

    def test_region_kinetic_and_binding_energy(
        self, sequence: TAbstractBaseSequence
    ) -> None:
        for r in sequence.regions:
            is_binding_energy = r.energy_mode == EnergyMode.BINDING
            is_kinetic_energy = r.energy_mode == EnergyMode.KINETIC
            assert r.is_binding_energy() == is_binding_energy
            assert r.is_binding_energy() != is_kinetic_energy
            assert r.is_kinetic_energy() == is_kinetic_energy
            assert r.is_kinetic_energy() != is_binding_energy

    def test_file_loads_into_class_with_expected_values(
        self,
        sequence: TAbstractBaseSequence,
        expected_region_values: list[dict[str, Any]],
    ) -> None:
        for i, r in enumerate(sequence.regions):
            for key in r.__dict__:
                if key in expected_region_values[i]:
                    assert r.__dict__[key] == expected_region_values[i][key]
                else:
                    raise KeyError('key "' + key + '" is not in the expected values.')


class TestSpecsSequenceAndRegions(
    TestAbstractSequenceAndRegions[SpecsSequence, SpecsRegion]
):
    @pytest.fixture
    def sequence_file(self) -> str:
        return "specs_sequence.seq"

    @pytest.fixture
    def sequence_class(self) -> type[SpecsSequence]:
        return SpecsSequence

    @pytest.fixture
    def expected_region_class(self) -> type[SpecsRegion]:
        return SpecsRegion

    @pytest.fixture
    def expected_region_values(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "region",
                "acquisition_mode": "Fixed Transmission",
                "psu_mode": "3.5kV",
                "lens_mode": "SmallArea",
                "low_energy": 800.0,
                "high_energy": 850.0,
                "energy_step": 0.1,
                "pass_energy": "5.0",
                "iterations": 1,
                "step_time": 1.0,
                "enabled": False,
                "energy_mode": EnergyMode.KINETIC,
                "values": 1,
                "slices": 100,
                "centre_energy": 0.0,
                "estimated_time_in_ms": 0,
            },
            {
                "name": "region2",
                "acquisition_mode": "Snapshot",
                "psu_mode": "1.5kV",
                "lens_mode": "LargeArea",
                "low_energy": 599.866,
                "high_energy": 600.134,
                "energy_step": 0.2680000000000291,
                "pass_energy": "2.0",
                "iterations": 5,
                "step_time": 2.0,
                "enabled": True,
                "energy_mode": EnergyMode.BINDING,
                "values": 1,
                "slices": 110,
                "centre_energy": 0.0,
                "estimated_time_in_ms": 13718,
            },
        ]


class TestVGScientaSequenceAndRegions(
    TestAbstractSequenceAndRegions[VGScientaSequence, VGScientaRegion]
):
    @pytest.fixture
    def sequence_file(self) -> str:
        return "vgscienta_sequence.seq"

    @pytest.fixture
    def sequence_class(self) -> type[VGScientaSequence]:
        return VGScientaSequence

    @pytest.fixture
    def expected_region_class(self) -> type[VGScientaRegion]:
        return VGScientaRegion

    @pytest.fixture
    def expected_region_values(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "New_Region",
                "enabled": True,
                "id": "_aQOmgPsmEe6w2YUF3bV-LA",
                "lens_mode": "Angular56",
                "pass_energy": "5",
                "slices": 1,
                "iterations": 1,
                "acquisition_mode": AcquisitionMode.SWEPT,
                "excitation_energy_source": "source2",
                "energy_mode": EnergyMode.KINETIC,
                "low_energy": 100.0,
                "high_energy": 101.0,
                "fix_energy": 9.0,
                "step_time": 1.0,
                "total_steps": 8.0,
                "total_time": 8.0,
                "energy_step": 200.0,
                "exposure_time": 1.0,
                "first_x_channel": 1,
                "last_x_channel": 1000,
                "first_y_channel": 101,
                "last_y_channel": 800,
                "detector_mode": DetectorMode.ADC,
                "status": Status.READY,
            },
            {
                "name": "New_Region1",
                "enabled": False,
                "id": "_aQOmgPsmEe6w2YUF3GV-LL",
                "lens_mode": "Angular45",
                "pass_energy": "10",
                "slices": 10,
                "iterations": 5,
                "acquisition_mode": AcquisitionMode.FIXED,
                "excitation_energy_source": "source1",
                "energy_mode": EnergyMode.BINDING,
                "low_energy": 4899.5615,
                "high_energy": 4900.4385,
                "fix_energy": 4900.0,
                "step_time": 0.882,
                "total_steps": 1.0,
                "total_time": 4.41,
                "energy_step": 0.877,
                "exposure_time": 1.0,
                "first_x_channel": 4,
                "last_x_channel": 990,
                "first_y_channel": 110,
                "last_y_channel": 795,
                "detector_mode": DetectorMode.PULSE_COUNTING,
                "status": Status.READY,
            },
        ]

    def test_sequence_get_expected_excitation_energy_source(
        self,
        sequence: VGScientaSequence,
    ) -> None:
        assert (
            sequence.get_excitation_energy_source_by_region(sequence.regions[0])
            == sequence.excitation_energy_sources[1]
        )
        assert (
            sequence.get_excitation_energy_source_by_region(sequence.regions[1])
            == sequence.excitation_energy_sources[0]
        )
        with pytest.raises(ValueError):
            sequence.get_excitation_energy_source_by_region(
                VGScientaRegion(excitation_energy_source="invalid_source")
            )
