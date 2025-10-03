import asyncio
from pathlib import Path, PurePath
from unittest.mock import patch

import pytest
from ophyd_async.core import PathProvider, StandardDetector, init_devices
from ophyd_async.sim import PatternGenerator, SimBlobDetector, SimMotor

from dodal.devices.common_dcm import BaseDCM
from dodal.devices.i03.dcm import DCM
from dodal.devices.undulator import Undulator
from tests.devices.test_data import (
    TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT,
)


class UndulatorGapCheckDevices:
    def __init__(self, undulator: Undulator, dcm: BaseDCM):
        self.undulator = undulator
        self.dcm = dcm


@pytest.fixture
async def mock_undulator_and_dcm() -> UndulatorGapCheckDevices:
    async with init_devices(mock=True):
        undulator = Undulator(
            "",
            id_gap_lookup_table_path=TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT,
        )
        dcm = DCM("")
    return UndulatorGapCheckDevices(undulator, dcm)


@pytest.fixture
def det(tmp_path: Path, path_provider) -> StandardDetector:
    class DevNullPatternGenerator(PatternGenerator):
        def __init__(self, sleep=asyncio.sleep):
            super().__init__(sleep)
            self.n_images = 0

        def open_file(self, path: PurePath, width: int, height: int):
            pass

        async def write_images_to_file(
            self, exposure: float, period: float, number_of_frames: int
        ):
            self.n_images += number_of_frames

        def generate_point(self, channel: int = 1, high_energy: bool = False) -> float:
            return 0.0

        async def wait_for_next_index(self, timeout: float):
            pass

        def get_last_index(self) -> int:
            return self.n_images

        def close_file(self):
            pass

    pattern_generator = DevNullPatternGenerator()
    with init_devices(mock=True):
        det = SimBlobDetector(path_provider, pattern_generator)
    return det


@pytest.fixture
def x_axis() -> SimMotor:
    with init_devices(mock=True):
        x_axis = SimMotor()
    return x_axis


@pytest.fixture
def y_axis() -> SimMotor:
    with init_devices(mock=True):
        y_axis = SimMotor()
    return y_axis


@pytest.fixture
def path_provider(static_path_provider: PathProvider):
    # Prevents issue with leftover state from beamline tests
    with patch("dodal.plan_stubs.data_session.get_path_provider") as mock:
        mock.return_value = static_path_provider
        yield static_path_provider
