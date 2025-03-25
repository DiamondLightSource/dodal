from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

import pytest

from dodal.devices.electron_analyser.abstract_region import (
    EnergyMode,
    TAbstractBaseRegion,
    TBaseSequence,
)
from dodal.devices.electron_analyser.specs_region import SpecsRegion, SpecsSequence
from dodal.devices.electron_analyser.vgscienta_region import (
    AcquisitionMode,
    DetectorMode,
    Status,
    VGScientaRegion,
    VGScientaSequence,
)


class TestAbstractSequenceAndRegions(ABC, Generic[TBaseSequence, TAbstractBaseRegion]):
    @pytest.fixture
    @abstractmethod
    def sequence_file(self) -> str:
        pass

    @pytest.fixture
    @abstractmethod
    def sequence_class(self) -> type[TBaseSequence]:
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
        self, sequence: TBaseSequence, expected_region_names: list[str]
    ) -> None:
        for name in expected_region_names:
            assert sequence.get_region_by_name(name) is not None
        assert (
            sequence.get_region_by_name("region name should not be in sequence") is None
        )

    def test_sequence_get_expected_region_type(
        self, sequence: TBaseSequence, expected_region_class: type[TAbstractBaseRegion]
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
        self, sequence: TBaseSequence, expected_region_names: list[str]
    ) -> None:
        assert sequence.get_region_names() == expected_region_names

    def test_sequence_get_expected_enabled_region_names(
        self, sequence: TBaseSequence, expected_enabled_region_names: list[str]
    ) -> None:
        assert sequence.get_enabled_region_names() == expected_enabled_region_names

    def test_region_kinetic_and_binding_energy(self, sequence: TBaseSequence) -> None:
        for r in sequence.regions:
            is_binding_energy = r.energyMode == EnergyMode.BINDING
            is_kinetic_energy = r.energyMode == EnergyMode.KINETIC
            assert r.is_binding_energy() == is_binding_energy
            assert r.is_binding_energy() != is_kinetic_energy
            assert r.is_kinetic_energy() == is_kinetic_energy
            assert r.is_kinetic_energy() != is_binding_energy

    def test_file_loads_into_class_with_expected_values(
        self, sequence: TBaseSequence, expected_region_values: list[dict[str, Any]]
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
                "acquisitionMode": "Fixed Transmission",
                "psuMode": "3.5kV",
                "lensMode": "SmallArea",
                "lowEnergy": 800.0,
                "highEnergy": 850.0,
                "energyStep": 0.1,
                "passEnergy": 5.0,
                "iterations": 1,
                "stepTime": 1.0,
                "enabled": False,
                "energyMode": EnergyMode.KINETIC,
                "values": 1,
                "slices": 100,
                "centreEnergy": 0.0,
                "estimatedTimeInMs": 0,
            },
            {
                "name": "region2",
                "acquisitionMode": "Snapshot",
                "psuMode": "1.5kV",
                "lensMode": "LargeArea",
                "lowEnergy": 599.866,
                "highEnergy": 600.134,
                "energyStep": 0.2680000000000291,
                "passEnergy": 2.0,
                "iterations": 5,
                "stepTime": 2.0,
                "enabled": True,
                "energyMode": EnergyMode.BINDING,
                "values": 1,
                "slices": 110,
                "centreEnergy": 0.0,
                "estimatedTimeInMs": 13718,
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
                "regionId": "_aQOmgPsmEe6w2YUF3bV-LA",
                "lensMode": "Angular56",
                "passEnergy": 5,
                "slices": 1,
                "iterations": 1,
                "acquisitionMode": AcquisitionMode.SWEPT,
                "excitationEnergySource": "source2",
                "energyMode": EnergyMode.KINETIC,
                "lowEnergy": 100.0,
                "highEnergy": 101.0,
                "fixEnergy": 9.0,
                "stepTime": 1.0,
                "totalSteps": 8.0,
                "totalTime": 8.0,
                "energyStep": 200.0,
                "exposureTime": 1.0,
                "firstXChannel": 1,
                "lastXChannel": 1000,
                "firstYChannel": 101,
                "lastYChannel": 800,
                "detectorMode": DetectorMode.ADC,
                "status": Status.READY,
            },
            {
                "name": "New_Region1",
                "enabled": False,
                "regionId": "_aQOmgPsmEe6w2YUF3GV-LL",
                "lensMode": "Angular45",
                "passEnergy": 10,
                "slices": 10,
                "iterations": 5,
                "acquisitionMode": AcquisitionMode.FIXED,
                "excitationEnergySource": "source1",
                "energyMode": EnergyMode.BINDING,
                "lowEnergy": 4899.5615,
                "highEnergy": 4900.4385,
                "fixEnergy": 4900.0,
                "stepTime": 0.882,
                "totalSteps": 1.0,
                "totalTime": 4.41,
                "energyStep": 0.877,
                "exposureTime": 1.0,
                "firstXChannel": 4,
                "lastXChannel": 990,
                "firstYChannel": 110,
                "lastYChannel": 795,
                "detectorMode": DetectorMode.PULSE_COUNTING,
                "status": Status.READY,
            },
        ]

    def test_sequence_get_expected_excitation_energy_source(
        self,
        sequence: VGScientaSequence,
    ) -> None:
        assert (
            sequence.get_excitation_energy_source_by_region(sequence.regions[0])
            == sequence.excitationEnergySources[1]
        )
        assert (
            sequence.get_excitation_energy_source_by_region(sequence.regions[1])
            == sequence.excitationEnergySources[0]
        )
        with pytest.raises(ValueError):
            sequence.get_excitation_energy_source_by_region(
                VGScientaRegion(excitationEnergySource="invalid_source")
            )
