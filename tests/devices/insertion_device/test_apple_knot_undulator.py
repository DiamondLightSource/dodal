import pytest

from dodal.devices.insertion_device import (
    I05_APPLE_KNOT_EXCLUSION_ZONES,
    AppleKnotController,
    AppleKnotPathFinder,
)
from dodal.devices.insertion_device.apple2_undulator import (
    Apple2,
    Apple2LockedPhasesVal,
    Apple2Val,
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


@pytest.mark.parametrize(
    "start_gap, start_phase, target_gap, target_phase",
    [
        (5.0, 10.0, 5.0, 10.0),
        (-50.0, 10.0, 50.0, 10.0),
    ],
)
def test_apple_knot_path_finder_empty(
    apple_knot_i05_path_finder: AppleKnotPathFinder,
    start_gap: float,
    start_phase: float,
    target_gap: float,
    target_phase: float,
) -> None:
    start_val = Apple2Val(
        gap=start_gap,
        phase=Apple2LockedPhasesVal(
            top_outer=start_phase,
            btm_inner=start_phase,
        ),
    )
    target_val = Apple2Val(
        gap=target_gap,
        phase=Apple2LockedPhasesVal(
            top_outer=target_phase,
            btm_inner=target_phase,
        ),
    )
    path = apple_knot_i05_path_finder.get_apple_knot_val_path(start_val, target_val)
    assert path == ()
