from abc import ABC, abstractmethod
from typing import Generic

import pytest
from bluesky.plan_stubs import abs_set
from bluesky.run_engine import RunEngine
from ophyd_async.testing import (
    get_mock_put,
)

from dodal.devices.electron_analyser.abstract_analyser_controller import (
    TAbstractAnalyserController,
)
from dodal.devices.electron_analyser.abstract_region import (
    TAbstractBaseRegion,
    TAbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs_analyser_controller import (
    SpecsAnalyserController,
)
from dodal.devices.electron_analyser.specs_region import SpecsRegion, SpecsSequence
from dodal.devices.electron_analyser.vgscienta_analyser_controller import (
    VGScientaAnalyserController,
)
from dodal.devices.electron_analyser.vgscienta_region import (
    VGScientaRegion,
    VGScientaSequence,
)


@pytest.fixture
def RE() -> RunEngine:
    return RunEngine()


class AbstractTestAnalyserController(
    ABC,
    Generic[TAbstractAnalyserController, TAbstractBaseSequence, TAbstractBaseRegion],
):
    @pytest.fixture
    @abstractmethod
    def analyser_type(self) -> type[TAbstractAnalyserController]:
        pass

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
    def excitation_energy_eV(self, *args, **kwargs) -> float:
        pass

    @pytest.fixture
    def region(
        self, request: pytest.FixtureRequest, sequence: TAbstractBaseSequence
    ) -> TAbstractBaseRegion:
        region = sequence.get_region_by_name(request.param)
        if region is None:
            raise ValueError("Region " + request.param + " is not found.")
        return region

    def test_analyser_to_kinetic_energy(
        self,
        sim_analyser: TAbstractAnalyserController,
        region: TAbstractBaseRegion,
        excitation_energy_eV: float,
    ) -> None:
        low_energy = region.lowEnergy
        ke = sim_analyser.to_kinetic_energy(
            low_energy, excitation_energy_eV, region.energyMode
        )
        if region.is_binding_energy():
            assert ke == (excitation_energy_eV - low_energy)
        else:
            assert ke == low_energy

    def test_given_region_that_analyser_sets_modes_correctly(
        self,
        sim_analyser: TAbstractAnalyserController,
        region: TAbstractBaseRegion,
        excitation_energy_eV: float,
        RE: RunEngine,
    ) -> None:
        RE(abs_set(sim_analyser, region, excitation_energy_eV))

        get_mock_put(sim_analyser.acquisition_mode).assert_called_once_with(
            region.acquisitionMode, wait=True
        )
        get_mock_put(sim_analyser.lens_mode).assert_called_once_with(
            region.lensMode, wait=True
        )

    def test_given_region_that_analyser_sets_energy_values_correctly(
        self,
        sim_analyser: TAbstractAnalyserController,
        region: TAbstractBaseRegion,
        excitation_energy_eV: float,
        RE: RunEngine,
    ) -> None:
        RE(abs_set(sim_analyser, region, excitation_energy_eV))

        expected_low_e = region.to_kinetic_energy(
            region.lowEnergy, excitation_energy_eV
        )
        expected_high_e = region.to_kinetic_energy(
            region.highEnergy, excitation_energy_eV
        )
        expected_pass_e = region.passEnergy

        get_mock_put(sim_analyser.low_energy).assert_called_once_with(
            expected_low_e, wait=True
        )
        get_mock_put(sim_analyser.high_energy).assert_called_once_with(
            expected_high_e, wait=True
        )
        get_mock_put(sim_analyser.pass_energy).assert_called_once_with(
            expected_pass_e, wait=True
        )

    def test_given_region_that_analyser_sets_channel_correctly(
        self,
        sim_analyser: TAbstractAnalyserController,
        region: TAbstractBaseRegion,
        excitation_energy_eV: float,
        RE: RunEngine,
    ) -> None:
        RE(abs_set(sim_analyser, region, excitation_energy_eV))

        expected_slices = region.slices
        expected_iterations = region.iterations
        get_mock_put(sim_analyser.slices).assert_called_once_with(
            expected_slices, wait=True
        )
        get_mock_put(sim_analyser.iterations).assert_called_once_with(
            expected_iterations, wait=True
        )


@pytest.mark.parametrize("region", ["region", "region2"], indirect=True)
class TestSpecsAnalyserController(
    AbstractTestAnalyserController[SpecsAnalyserController, SpecsSequence, SpecsRegion]
):
    @pytest.fixture
    def analyser_type(self) -> type[SpecsAnalyserController]:
        return SpecsAnalyserController

    @pytest.fixture
    def sequence_file(self) -> str:
        return "specs_sequence.seq"

    @pytest.fixture
    def sequence_class(self) -> type[SpecsSequence]:
        return SpecsSequence

    @pytest.fixture
    def excitation_energy_eV(self) -> float:
        return 1000.0

    def test_given_region_that_analyser_sets_energy_values_correctly(
        self,
        sim_analyser: SpecsAnalyserController,
        region: SpecsRegion,
        excitation_energy_eV: float,
        RE: RunEngine,
    ) -> None:
        super().test_given_region_that_analyser_sets_energy_values_correctly(
            sim_analyser, region, excitation_energy_eV, RE
        )

        expected_step_e = region.get_energy_step_eV()
        if region.acquisitionMode == "Fixed Energy":
            get_mock_put(sim_analyser.energy_step).assert_called_once_with(
                expected_step_e, wait=True
            )
        else:
            get_mock_put(sim_analyser.energy_step).assert_not_called()

        if region.acquisitionMode == "Fixed Transmission":
            get_mock_put(sim_analyser.centre_energy).assert_called_once_with(
                region.centreEnergy, wait=True
            )
        else:
            get_mock_put(sim_analyser.centre_energy).assert_not_called()

    def test_given_region_that_analyser_sets_modes_correctly(
        self,
        sim_analyser: SpecsAnalyserController,
        region: SpecsRegion,
        excitation_energy_eV: float,
        RE: RunEngine,
    ) -> None:
        super().test_given_region_that_analyser_sets_modes_correctly(
            sim_analyser, region, excitation_energy_eV, RE
        )
        get_mock_put(sim_analyser.psu_mode).assert_called_once_with(
            region.psuMode, wait=True
        )


@pytest.mark.parametrize("region", ["New_Region", "New_Region1"], indirect=True)
class TestVGScientaAnalyserController(
    AbstractTestAnalyserController[
        VGScientaAnalyserController, VGScientaSequence, VGScientaRegion
    ]
):
    @pytest.fixture
    def sequence_file(self) -> str:
        return "vgscienta_sequence.seq"

    @pytest.fixture
    def sequence_class(self) -> type[VGScientaSequence]:
        return VGScientaSequence

    @pytest.fixture
    def excitation_energy_eV(
        self, region: VGScientaRegion, sequence: VGScientaSequence
    ) -> float:
        return sequence.get_excitation_energy_source_by_region(region).value

    @pytest.fixture
    def analyser_type(self) -> type[VGScientaAnalyserController]:
        return VGScientaAnalyserController

    def test_given_region_that_analyser_sets_modes_correctly(
        self,
        sim_analyser: VGScientaAnalyserController,
        region: VGScientaRegion,
        excitation_energy_eV: float,
        RE: RunEngine,
    ) -> None:
        super().test_given_region_that_analyser_sets_modes_correctly(
            sim_analyser, region, excitation_energy_eV, RE
        )

        get_mock_put(sim_analyser.detector_mode).assert_called_once_with(
            region.detectorMode, wait=True
        )
        get_mock_put(sim_analyser.image_mode).assert_called_once_with(
            "Single", wait=True
        )

    def test_given_region_that_analyser_sets_energy_values_correctly(
        self,
        sim_analyser: VGScientaAnalyserController,
        region: VGScientaRegion,
        excitation_energy_eV: float,
        RE: RunEngine,
    ) -> None:
        super().test_given_region_that_analyser_sets_energy_values_correctly(
            sim_analyser, region, excitation_energy_eV, RE
        )

        expected_centre_e = region.to_kinetic_energy(
            region.fixEnergy, excitation_energy_eV
        )
        expected_step_e = region.get_energy_step_eV()

        get_mock_put(sim_analyser.centre_energy).assert_called_once_with(
            expected_centre_e, wait=True
        )
        get_mock_put(sim_analyser.energy_step).assert_called_once_with(
            expected_step_e, wait=True
        )

    def test_given_region_that_analyser_sets_channel_correctly(
        self,
        sim_analyser: VGScientaAnalyserController,
        region: VGScientaRegion,
        excitation_energy_eV: float,
        RE: RunEngine,
    ) -> None:
        super().test_given_region_that_analyser_sets_channel_correctly(
            sim_analyser, region, excitation_energy_eV, RE
        )

        expected_first_x = region.firstXChannel
        expected_size_x = region.x_channel_size()
        get_mock_put(sim_analyser.first_x_channel).assert_called_once_with(
            expected_first_x, wait=True
        )
        get_mock_put(sim_analyser.x_channel_size).assert_called_once_with(
            expected_size_x, wait=True
        )

        expected_first_y = region.firstYChannel
        expected_size_y = region.y_channel_size()
        get_mock_put(sim_analyser.first_y_channel).assert_called_once_with(
            expected_first_y, wait=True
        )
        get_mock_put(sim_analyser.y_channel_size).assert_called_once_with(
            expected_size_y, wait=True
        )
