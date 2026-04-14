import pytest
from ophyd_async.core import (
    set_mock_value,
)

from dodal.devices.beamlines.i05_shared import (
    energy_to_gap_converter,
    energy_to_phase_converter,
)
from dodal.devices.insertion_device import (
    AppleKnotController,
    AppleKnotPathFinder,
    Pol,
)
from dodal.devices.insertion_device.apple2_undulator import (
    Apple2,
    UndulatorLockedPhaseAxes,
)

# add mock_config_client, mock_id_gap, mock_phase and mock_jaw_phase_axes to pytest.
pytest_plugins = [
    "dodal.testing.fixtures.devices.apple2",
    "dodal.testing.fixtures.devices.apple_knot",
]


@pytest.fixture
async def mock_apple_knot_i05_controller(
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    apple_knot_i05_path_finder: AppleKnotPathFinder,
) -> AppleKnotController[UndulatorLockedPhaseAxes]:
    mock_apple_knot_controller = AppleKnotController[UndulatorLockedPhaseAxes](
        apple=mock_locked_apple2,
        gap_energy_motor_converter=energy_to_gap_converter,
        phase_energy_motor_converter=energy_to_phase_converter,
        path_finder=apple_knot_i05_path_finder,
    )
    return mock_apple_knot_controller


@pytest.mark.parametrize(
    "target_energy, initial_gap, initial_phase_top_outer, expected_pol",
    [
        (100.0, 40.0, 70.0, Pol.LV),
        (100.0, 40.0, -70.0, Pol.LV),
        (100.0, 40.0, 0.0, Pol.LH),
        (50.0, 40.0, 0.0, Pol.LH),
        (60.0, 40.0, -50.0, Pol.NC),
        (60.0, 40.0, 50.0, Pol.PC),
    ],
)
async def test_id_set_energy_const_pol(
    mock_apple_knot_i05_controller: AppleKnotController[UndulatorLockedPhaseAxes],
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    target_energy: float,
    initial_gap: float,
    initial_phase_top_outer: float,
    expected_pol: Pol,
):
    set_mock_value(
        mock_locked_apple2.phase().top_outer.user_readback, initial_phase_top_outer
    )
    set_mock_value(
        mock_locked_apple2.phase().btm_inner.user_readback, initial_phase_top_outer
    )
    set_mock_value(mock_locked_apple2.gap().user_readback, initial_gap)
    assert await mock_apple_knot_i05_controller.polarisation.get_value() == expected_pol
    await mock_apple_knot_i05_controller.energy.set(target_energy)
    assert await mock_apple_knot_i05_controller.polarisation.get_value() == expected_pol
    assert await mock_apple_knot_i05_controller.energy.get_value() == target_energy


@pytest.mark.parametrize(
    "initial_pol, initial_energy, target_pol",
    [
        (Pol.LV, 40.0, Pol.LH),
        (Pol.LV, 40.0, Pol.LH),
        (Pol.LV, 80.0, Pol.PC),
        (Pol.LV, 80.0, Pol.NC),
    ],
)
async def test_id_set_pol(
    mock_apple_knot_i05_controller: AppleKnotController[UndulatorLockedPhaseAxes],
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    initial_pol: Pol,
    initial_energy: float,
    target_pol: Pol,
):
    mock_apple_knot_i05_controller._energy_set(initial_energy)
    set_mock_value(
        mock_locked_apple2.gap().user_readback,
        energy_to_gap_converter(initial_energy, initial_pol),
    )
    set_mock_value(
        mock_locked_apple2.phase().top_outer.user_readback,
        energy_to_phase_converter(initial_energy, initial_pol),
    )
    set_mock_value(
        mock_locked_apple2.phase().btm_inner.user_readback,
        energy_to_phase_converter(initial_energy, initial_pol),
    )
    assert await mock_apple_knot_i05_controller.polarisation.get_value() == initial_pol
    await mock_apple_knot_i05_controller.polarisation.set(target_pol)
    assert await mock_apple_knot_i05_controller.polarisation.get_value() == target_pol


@pytest.mark.parametrize(
    "initial_pol, initial_energy, target_pol",
    [
        (Pol.LV, 40.0, Pol.LA),
        (Pol.LV, 40.0, Pol.LH3),
        (Pol.LV, 80.0, Pol.LV3),
        (Pol.LV, 80.0, Pol.NONE),
    ],
)
async def test_id_set_pol_fails(
    mock_apple_knot_i05_controller: AppleKnotController[UndulatorLockedPhaseAxes],
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    initial_pol: Pol,
    initial_energy: float,
    target_pol: Pol,
):
    mock_apple_knot_i05_controller._energy_set(initial_energy)
    set_mock_value(
        mock_locked_apple2.gap().user_readback,
        energy_to_gap_converter(initial_energy, initial_pol),
    )
    set_mock_value(
        mock_locked_apple2.phase().top_outer.user_readback,
        energy_to_phase_converter(initial_energy, initial_pol),
    )
    set_mock_value(
        mock_locked_apple2.phase().btm_inner.user_readback,
        energy_to_phase_converter(initial_energy, initial_pol),
    )
    assert await mock_apple_knot_i05_controller.polarisation.get_value() == initial_pol
    with pytest.raises(
        RuntimeError,
        match="No valid path found for move avoiding exclusion zones.",
    ):
        await mock_apple_knot_i05_controller.polarisation.set(target_pol)


@pytest.mark.parametrize(
    "target_energy, initial_gap, initial_phase_top_outer",
    [
        (100.0, 10.0, 0.0),  # LH start point in exclusion zone
        (1.0, 10.0, 0.0),  # LH -> end point in exclusion zone
        (1.0, 29.0, 60.0),  # CR -> end point in exclusion zone
    ],
)
async def test_id_set_fails_exclusion_zone(
    mock_apple_knot_i05_controller: AppleKnotController[UndulatorLockedPhaseAxes],
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    target_energy: float,
    initial_gap: float,
    initial_phase_top_outer: float,
):
    set_mock_value(
        mock_locked_apple2.phase().top_outer.user_readback, initial_phase_top_outer
    )
    set_mock_value(
        mock_locked_apple2.phase().btm_inner.user_readback, initial_phase_top_outer
    )
    set_mock_value(mock_locked_apple2.gap().user_readback, initial_gap)
    with pytest.raises(
        RuntimeError,
        match="No valid path found for move avoiding exclusion zones.",
    ):
        await mock_apple_knot_i05_controller.energy.set(target_energy)


@pytest.mark.parametrize(
    "initial_phase_top_outer, initial_phase_bottom_inner",
    [
        (0.0, 0.1),
    ],
)
async def test_id_set_fails_top_bottom_phase_mismatch(
    mock_apple_knot_i05_controller: AppleKnotController[UndulatorLockedPhaseAxes],
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    initial_phase_top_outer: float,
    initial_phase_bottom_inner: float,
):
    set_mock_value(
        mock_locked_apple2.phase().top_outer.user_readback, initial_phase_top_outer
    )
    set_mock_value(
        mock_locked_apple2.phase().btm_inner.user_readback, initial_phase_bottom_inner
    )
    set_mock_value(mock_locked_apple2.gap().user_readback, 50.0)
    with pytest.raises(
        RuntimeError,
        match=f"Upper phase {initial_phase_top_outer} and lower phase {initial_phase_bottom_inner} values are not close enough.",
    ):
        await mock_apple_knot_i05_controller.energy.set(10.0)
