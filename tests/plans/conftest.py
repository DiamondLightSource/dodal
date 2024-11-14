from pathlib import Path
from unittest.mock import patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, PathProvider, StandardDetector
from ophyd_async.sim.demo import PatternDetector, SimMotor


@pytest.fixture
def det(
    RE: RunEngine,
    tmp_path: Path,
    path_provider,
) -> StandardDetector:
    with DeviceCollector(mock=True):
        det = PatternDetector(tmp_path / "foo.h5")
    return det


@pytest.fixture
def x_axis(RE: RunEngine) -> SimMotor:
    with DeviceCollector(mock=True):
        x_axis = SimMotor()
    return x_axis


@pytest.fixture
def y_axis(RE: RunEngine) -> SimMotor:
    with DeviceCollector(mock=True):
        y_axis = SimMotor()
    return y_axis


@pytest.fixture
def path_provider(static_path_provider: PathProvider):
    # Prevents issue with leftover state from beamline tests
    with patch("dodal.plan_stubs.data_session.get_path_provider") as mock:
        mock.return_value = static_path_provider
        yield
