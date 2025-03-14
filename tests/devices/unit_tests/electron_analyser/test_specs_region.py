from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.specs.specs_region import SpecsSequence


def test_specs_file_loads_into_class():
    file = "tests/test_data/electron_analyser/specs_sequence.seq"
    sequence = load_json_file_to_class(SpecsSequence, file)

    assert sequence.get_region_names() == ["Region1", "Region2"]
    assert sequence.get_enabled_region_names() == ["Region1"]
