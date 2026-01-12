import pytest

from dodal.common.maths import Rectangle2D
from dodal.devices.insertion_device import AppleKnotController
from dodal.devices.insertion_device.apple2_undulator import (
    Apple2,
    UndulatorLockedPhaseAxes,
)

# add mock_config_client, mock_id_gap, mock_phase and mock_jaw_phase_axes to pytest.
pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


@pytest.fixture
def configured_gap() -> float:
    return 42.0


@pytest.fixture
def configured_phase() -> float:
    return 7.5


@pytest.fixture
async def mock_locked_controller(
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    configured_gap: float,
    configured_phase: float,
) -> AppleKnotController:
    mock_apple_knot_controller = AppleKnotController(
        apple=mock_locked_apple2,
        gap_energy_motor_converter=lambda energy, pol: configured_gap,
        phase_energy_motor_converter=lambda energy, pol: configured_phase,
        exclusion_zone=[
            Rectangle2D(0, 0, 1, 1),
            Rectangle2D(0, 0, 1, 1),
        ],  # Dummy exclusion zone
    )
    return mock_apple_knot_controller
