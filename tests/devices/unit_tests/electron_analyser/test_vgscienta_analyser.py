import pytest
from bluesky.plan_stubs import abs_set
from bluesky.run_engine import RunEngine

from dodal.devices.electron_analyser.vgscienta.vgscienta_analyser import (
    VGScientaAnalyser,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_region import (
    VGScientaSequence,
)


@pytest.fixture
def analyser_type() -> type[VGScientaAnalyser]:
    return VGScientaAnalyser


@pytest.fixture
def sequence_file() -> str:
    return "vgscienta_sequence.seq"


@pytest.fixture
def sequence_class() -> type[VGScientaSequence]:
    return VGScientaSequence


def test_analyser_abs_set(
    sim_analyser: VGScientaAnalyser, sequence: VGScientaSequence
) -> None:
    RE = RunEngine()
    for r in sequence.get_enabled_regions():
        excitation_energy_source = sequence.get_excitation_energy_source_by_region(r)
        excitation_energy = excitation_energy_source.value
        RE(abs_set(sim_analyser, r, excitation_energy))
