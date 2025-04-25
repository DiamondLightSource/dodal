from pathlib import Path
from unittest.mock import patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import PathProvider, StandardDetector, init_devices
from ophyd_async.sim import PatternGenerator, SimBlobDetector, SimMotor
from tests.constants import UNDULATOR_ID_GAP_LOOKUP_TABLE_PATH

from dodal.devices.common_dcm import BaseDCM
from dodal.devices.i03.dcm import DCM
from dodal.devices.undulator import Undulator


class UndulatorGapCheckDevices:
    def __init__(self, undulator: Undulator, dcm: BaseDCM):
        self.undulator = undulator
        self.dcm = dcm


@pytest.fixture
async def mock_undulator_and_dcm() -> UndulatorGapCheckDevices:
    async with init_devices(mock=True):
        undulator = Undulator(
            "",
            id_gap_lookup_table_path=UNDULATOR_ID_GAP_LOOKUP_TABLE_PATH,
        )
        dcm = DCM("")
    return UndulatorGapCheckDevices(undulator, dcm)


@pytest.fixture
def det(
    RE: RunEngine,
    tmp_path: Path,
    path_provider,
) -> StandardDetector:
    pattern_generator = PatternGenerator()
    with init_devices(mock=True):
        det = SimBlobDetector(path_provider, pattern_generator)
    return det


@pytest.fixture
def x_axis(RE: RunEngine) -> SimMotor:
    with init_devices(mock=True):
        x_axis = SimMotor()
    return x_axis


@pytest.fixture
def y_axis(RE: RunEngine) -> SimMotor:
    with init_devices(mock=True):
        y_axis = SimMotor()
    return y_axis


@pytest.fixture
def path_provider(static_path_provider: PathProvider):
    # Prevents issue with leftover state from beamline tests
    with patch("dodal.plan_stubs.data_session.get_path_provider") as mock:
        mock.return_value = static_path_provider
        yield static_path_provider
