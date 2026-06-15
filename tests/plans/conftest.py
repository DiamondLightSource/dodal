import asyncio
from pathlib import Path, PurePath
from unittest.mock import patch

import pytest
from daq_config_server import ConfigClient
from ophyd_async.core import (
    PathProvider,
    StandardDetector,
    init_devices,
)
from ophyd_async.sim import PatternGenerator, SimBlobDetector, SimMotor

from dodal.devices.beamlines.i03.dcm import DCM
from dodal.devices.common_dcm import DoubleCrystalMonochromatorBase
from dodal.devices.undulator import UndulatorInKeV
from tests.devices.test_data import (
    TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT,
)


class UndulatorGapCheckDevices:
    def __init__(self, undulator: UndulatorInKeV, dcm: DoubleCrystalMonochromatorBase):
        self.undulator = undulator
        self.dcm = dcm


@pytest.fixture
async def mock_undulator_and_dcm() -> UndulatorGapCheckDevices:
    async with init_devices(mock=True):
        undulator = UndulatorInKeV(
            "",
            ConfigClient(""),
            id_gap_lookup_table_path=TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT,
        )
        dcm = DCM("")
    return UndulatorGapCheckDevices(undulator, dcm)


@pytest.fixture
def det(tmp_path: Path, path_provider) -> StandardDetector:
    class DevNullPatternGenerator(PatternGenerator):
        def __init__(self, sleep=asyncio.sleep):
            super().__init__(sleep)
            self._written = 0

        def open_file(self, path: PurePath, width: int, height: int):
            self._update_images_written(0)

        def setup_acquisition_parameters(
            self, exposure: float, period: float, number_of_frames: int
        ):
            self._number_of_frames = number_of_frames

        async def write_images_to_file(self):
            self._written += 1
            self._update_images_written(self._written)

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
def z_axis() -> SimMotor:
    with init_devices(mock=True):
        z_axis = SimMotor()
    return z_axis


@pytest.fixture
def path_provider(static_path_provider: PathProvider):
    # Prevents issue with leftover state from beamline tests
    with patch("dodal.plan_stubs.data_session.get_path_provider") as mock:
        mock.return_value = static_path_provider
        yield static_path_provider
