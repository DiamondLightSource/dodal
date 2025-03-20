import pytest

from dodal.devices.electron_analyser.specs_analyser import SpecsAnalyser
from dodal.devices.electron_analyser.specs_region import SpecsSequence


@pytest.fixture
def analyser_type() -> type[SpecsAnalyser]:
    return SpecsAnalyser


@pytest.fixture
def sequence_file() -> str:
    return "specs_sequence.seq"


@pytest.fixture
def sequence_class() -> type[SpecsSequence]:
    return SpecsSequence


async def test_analyser_set(
    sim_analyser: SpecsAnalyser, sequence: SpecsSequence
) -> None:
    for r in sequence.get_enabled_regions():
        excitation_energy = 100
        await sim_analyser.set(r, excitation_energy)
