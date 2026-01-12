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
    "start_phase, start_gap, target_phase, target_gap",
    [
        (5.0, 10.0, 5.0, 10.0),
        (-50.0, 10.0, 50.0, 10.0),
        (-10.0, 37.0, 50.0, 10.0),
        (-10.0, 37.0, 70.0, 10.0),
        (35.0, 35.0, 50.0, 10.0),
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


@pytest.mark.parametrize(
    "start_phase, start_gap, target_phase, target_gap",
    [
        # constant phase moves
        (0.0, 88.0, 0.0, 65.0),
        (0.0, 66.0, 0.0, 77.0),
        (25.0, 30.0, 25.0, 65.0),
        (25.0, 65.0, 25.0, 30.0),
        (-25.0, 60.0, -25.0, 45.0),
        (-25.0, 45.0, -25.0, 61.0),
        # constant gap moves
        (-10.0, 50.0, 0.0, 50.0),
        (0.0, 50.0, 20.0, 50.0),
        (-20.0, 50.0, -10.0, 50.0),
        (-10.0, 50.0, -20.0, 50.0),
        (20.0, 40.0, 10.0, 40.0),
        (40.0, 40.0, 20.0, 40.0),
    ],
)
def test_apple_knot_path_finder_direct_path(
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
    assert path == (start_val, target_val)


@pytest.mark.parametrize(
    "start_phase, start_gap, target_phase, target_gap",
    [
        (0.0, 65.0, 70.0, 40.0),  # positive phase SE
        (0.0, 65.0, -70.0, 40.0),  # negative phase SW
    ],
)
def test_apple_knot_path_finder_phase_gap_order(
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
    intermediate_val = Apple2Val(
        gap=start_gap,
        phase=Apple2LockedPhasesVal(
            top_outer=target_phase,
            btm_inner=target_phase,
        ),
    )
    path = apple_knot_i05_path_finder.get_apple_knot_val_path(start_val, target_val)
    assert path == (start_val, intermediate_val, target_val)


@pytest.mark.parametrize(
    "start_phase, start_gap, target_phase, target_gap",
    [
        (70.0, 54.0, 0.0, 88.0),  # positive phase NW
        (70.0, 54.0, 80.0, 88.0),  # positive phase NE
        (70.0, 88.0, 50.0, 60.0),  # positive phase SW
        (-70.0, 44.0, -80.0, 88.0),  # negative phase NW
        (-70.0, 54.0, 0.0, 88.0),  # negative phase NE
        (-70.0, 88.0, 0.0, 78.0),  # negative phase SE
    ],
)
def test_apple_knot_path_finder_gap_phase_order(
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
    intermediate_val = Apple2Val(
        gap=target_gap,
        phase=Apple2LockedPhasesVal(
            top_outer=start_phase,
            btm_inner=start_phase,
        ),
    )
    path = apple_knot_i05_path_finder.get_apple_knot_val_path(start_val, target_val)
    assert path == (start_val, intermediate_val, target_val)


@pytest.mark.parametrize(
    "start_phase, start_gap, target_phase, target_gap",
    [
        (-50.0, 70.0, 20.0, 30.0),  # gp+pg, cross zero phase at mean of gap
        (67.0, 10.0, -69.0, 20.0),  # gp+pg, cross zero phase at max exclusion zone
    ],
)
def test_apple_knot_path_finder_cross_zero(
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
    zero_phase_val = apple_knot_i05_path_finder.get_zero_phase_crossing_point(
        start_val, target_val
    )
    intermediate_neg_phase_val = Apple2Val(
        gap=zero_phase_val.gap,
        phase=Apple2LockedPhasesVal(
            top_outer=start_phase,
            btm_inner=start_phase,
        ),
    )
    intermediate_pos_phase_val = Apple2Val(
        gap=zero_phase_val.gap,
        phase=Apple2LockedPhasesVal(
            top_outer=target_phase,
            btm_inner=target_phase,
        ),
    )
    path = apple_knot_i05_path_finder.get_apple_knot_val_path(start_val, target_val)
    assert path == (
        start_val,
        intermediate_neg_phase_val,
        zero_phase_val,
        intermediate_pos_phase_val,
        target_val,
    )


@pytest.mark.parametrize(
    "start_phase, start_gap, target_phase, target_gap",
    [
        (-70.0, 10.0, 69.0, 60.0),  # gp+gp, cross zero phase at mean of gaps
    ],
)
def test_apple_knot_path_finder_gap_phase_order_cross_zero(
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
    zero_phase_val = apple_knot_i05_path_finder.get_zero_phase_crossing_point(
        start_val, target_val
    )
    intermediate_neg_phase_val = Apple2Val(
        gap=zero_phase_val.gap,
        phase=Apple2LockedPhasesVal(
            top_outer=start_phase,
            btm_inner=start_phase,
        ),
    )
    intermediate_pos_phase_val = Apple2Val(
        gap=target_gap,
        phase=Apple2LockedPhasesVal(
            top_outer=zero_phase_val.phase.top_outer,
            btm_inner=zero_phase_val.phase.btm_inner,
        ),
    )
    path = apple_knot_i05_path_finder.get_apple_knot_val_path(start_val, target_val)
    assert path == (
        start_val,
        intermediate_neg_phase_val,
        zero_phase_val,
        intermediate_pos_phase_val,
        target_val,
    )
