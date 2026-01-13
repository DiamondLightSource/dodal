import pytest

from dodal.devices.insertion_device import (
    I05_APPLE_KNOT_EXCLUSION_ZONES,
    AppleKnotController,
    AppleKnotPathFinder,
)
from dodal.devices.insertion_device.apple2_undulator import (
    Apple2,
    UndulatorLockedPhaseAxes,
)

# add mock_config_client, mock_id_gap, mock_phase and mock_jaw_phase_axes to pytest.
pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


@pytest.fixture
def apple_knot_i05_path_finder() -> AppleKnotPathFinder:
    return AppleKnotPathFinder(I05_APPLE_KNOT_EXCLUSION_ZONES)


@pytest.fixture
def configured_gap() -> float:
    return 42.0


@pytest.fixture
def configured_phase() -> float:
    return 7.5


@pytest.fixture
async def mock_apple_knot_i05_locked_controller(
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    configured_gap: float,
    configured_phase: float,
    apple_knot_i05_path_finder: AppleKnotPathFinder,
) -> AppleKnotController:
    mock_apple_knot_controller = AppleKnotController(
        apple=mock_locked_apple2,
        gap_energy_motor_converter=lambda energy, pol: configured_gap,
        phase_energy_motor_converter=lambda energy, pol: configured_phase,
        path_finder=apple_knot_i05_path_finder,
    )
    return mock_apple_knot_controller
