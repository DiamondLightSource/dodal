import pytest
from ophyd_async.core import DeviceCollector

from dodal.devices.undulator import Undulator

SIM_INSERTION_PREFIX = "SR03S"

ID_GAP_LOOKUP_TABLE_PATH: str = (
    "./tests/devices/unit_tests/test_beamline_undulator_to_gap_lookup_table.txt"
)


@pytest.mark.s03
def test_undulator_connects():
    with DeviceCollector():
        undulator = Undulator(  # noqa: F841
            f"{SIM_INSERTION_PREFIX}-MO-SERVC-01:",
            id_gap_lookup_table_path=ID_GAP_LOOKUP_TABLE_PATH,
        )
