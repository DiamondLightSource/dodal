import pytest
from ophyd_async.core import init_devices
from tests.constants import UNDULATOR_ID_GAP_LOOKUP_TABLE_PATH

from dodal.devices.undulator import Undulator

SIM_INSERTION_PREFIX = "SR03S"


@pytest.mark.s03
def test_undulator_connects():
    with init_devices():
        undulator = Undulator(  # noqa: F841
            f"{SIM_INSERTION_PREFIX}-MO-SERVC-01:",
            id_gap_lookup_table_path=UNDULATOR_ID_GAP_LOOKUP_TABLE_PATH,
        )
