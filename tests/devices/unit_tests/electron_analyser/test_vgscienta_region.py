from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.vgscienta.vgscienta_region import VGScientaSequence


def test_vgscienta_file_loads_into_class():
    file = "tests/test_data/electron_analyser/vgscienta_sequence.seq"
    sequence = load_json_file_to_class(VGScientaSequence, file)

    assert sequence.get_region_names() == ["New_Region1", "New_Region2"]
    assert sequence.get_enabled_region_names() == ["New_Region1"]

    assert (
        sequence.get_excitation_energy_source_by_region(sequence.regions[0])
        == sequence.excitationEnergySources[0]
    )
    assert (
        sequence.get_excitation_energy_source_by_region(sequence.regions[1])
        == sequence.excitationEnergySources[1]
    )
