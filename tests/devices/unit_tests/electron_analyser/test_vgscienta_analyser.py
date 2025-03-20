import pytest

from dodal.devices.electron_analyser.vgscienta_analyser import VGScientaAnalyser
from dodal.devices.electron_analyser.vgscienta_region import VGScientaSequence


@pytest.fixture
def analyser_type() -> type[VGScientaAnalyser]:
    return VGScientaAnalyser


@pytest.fixture
def sequence_file() -> str:
    return "vgscienta_sequence.seq"


@pytest.fixture
def sequence_class() -> type[VGScientaSequence]:
    return VGScientaSequence


async def test_analyser_abs_set(
    sim_analyser: VGScientaAnalyser, sequence: VGScientaSequence
) -> None:
    for r in sequence.get_enabled_regions():
        excitation_energy_source = sequence.get_excitation_energy_source_by_region(r)
        excitation_energy = excitation_energy_source.value
        await sim_analyser.set(r, excitation_energy)
