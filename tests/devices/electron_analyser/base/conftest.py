import pytest

from dodal.devices.electron_analyser.base import ElectronAnalyserDetector


@pytest.fixture(params=["ew4000", "b07b_specs150"])
def sim_detector(request: pytest.FixtureRequest) -> ElectronAnalyserDetector:
    return request.getfixturevalue(request.param)
