import pytest
from bluesky.plan_stubs import abs_set
from bluesky.run_engine import RunEngine

from dodal.devices.electron_analyser.specs.specs_analyser import SpecsAnalyser
from dodal.devices.electron_analyser.specs.specs_region import (
    SpecsSequence,
)


@pytest.fixture
def analyser_type() -> type[SpecsAnalyser]:
    return SpecsAnalyser


@pytest.fixture
def sequence_file() -> str:
    return "specs_sequence.seq"


@pytest.fixture
def sequence_class() -> type[SpecsSequence]:
    return SpecsSequence


def test_analyser_abs_set(sim_analyser: SpecsAnalyser, sequence: SpecsSequence) -> None:
    RE = RunEngine()
    excitation_energy = 100
    for r in sequence.get_enabled_regions():
        RE(abs_set(sim_analyser, r, excitation_energy))
