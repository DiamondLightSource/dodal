import os

from tests.devices.unit_tests.electron_analyser.utils import (
    TEST_DATA_PATH,
    check_region_model_list_to_expected_values,
)

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.base_region import EnergyMode
from dodal.devices.electron_analyser.vgscienta.vgscienta_region import (
    AcquisitionMode,
    DetectorMode,
    Status,
    VGScientaSequence,
)


def get_expected_region_values():
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


def test_vgscienta_file_loads_into_class():
    file = os.path.join(TEST_DATA_PATH, "vgscienta_sequence.seq")
    sequence = load_json_file_to_class(VGScientaSequence, file)

    assert sequence.get_region_names() == ["New_Region", "New_Region1"]
    assert sequence.get_enabled_region_names() == ["New_Region"]

    assert (
        sequence.get_excitation_energy_source_by_region(sequence.regions[0])
        == sequence.excitationEnergySources[1]
    )
    assert (
        sequence.get_excitation_energy_source_by_region(sequence.regions[1])
        == sequence.excitationEnergySources[0]
    )
    check_region_model_list_to_expected_values(
        sequence.regions, get_expected_region_values()
    )
