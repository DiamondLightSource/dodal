import numpy.polynomial as poly
import pytest
from ophyd_async.core import (
    set_mock_value,
)

from dodal.devices.insertion_device import (
    I05_APPLE_KNOT_EXCLUSION_ZONES,
    AppleKnotController,
    AppleKnotPathFinder,
    Pol,
)
from dodal.devices.insertion_device.apple2_undulator import (
    Apple2,
    UndulatorLockedPhaseAxes,
)

# add mock_config_client, mock_id_gap, mock_phase and mock_jaw_phase_axes to pytest.
pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]

LH_GAP_POLYNOMIAL = poly.Polynomial(
    [
        12.464,
        11.8417,
        -0.030139,
        0.00023511,
        1.0158e-6,
        -3.9229e-8,
        3.6772e-10,
        -1.7356e-12,
        4.2103e-15,
        -4.1724e-18,
    ]
)

LV_GAP_POLYNOMIAL = poly.Polynomial(
    [
        8.7456,
        1.1344,
        -0.024317,
        0.00041143,
        -5.0759e-6,
        4.496e-8,
        -2.7464e-10,
        1.081e-12,
        -2.4377e-15,
        2.3749e-18,
    ]
)


def configured_gap(energy: float, pol: Pol) -> float:
    if pol == Pol.LH:
        return float(LH_GAP_POLYNOMIAL(energy))
    if pol == Pol.LV:
        return float(LV_GAP_POLYNOMIAL(energy))
    return 1.0


@pytest.fixture
def apple_knot_i05_path_finder() -> AppleKnotPathFinder:
    return AppleKnotPathFinder(I05_APPLE_KNOT_EXCLUSION_ZONES)


@pytest.fixture
def configured_phase() -> float:
    return 70.0


@pytest.fixture
async def mock_apple_knot_i05_controller(
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    configured_phase: float,
    apple_knot_i05_path_finder: AppleKnotPathFinder,
) -> AppleKnotController:
    mock_apple_knot_controller = AppleKnotController(
        apple=mock_locked_apple2,
        gap_energy_motor_converter=configured_gap,
        phase_energy_motor_converter=lambda energy, pol: configured_phase,
        path_finder=apple_knot_i05_path_finder,
    )
    return mock_apple_knot_controller


@pytest.mark.parametrize(
    "energy, initial_gap, initial_phase_top_outer, initial_pol",
    [
        (100.0, 40.0, 70.0, Pol.LV),
        (100.0, 40.0, 70.0, Pol.LV),
    ],
)
async def test_id_set_energy_no_change_in_polarisation(
    mock_apple_knot_i05_controller: AppleKnotController,
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    energy: float,
    initial_gap: float,
    initial_phase_top_outer: float,
    initial_pol: Pol,
):
    set_mock_value(
        mock_locked_apple2.phase().top_outer.user_readback, initial_phase_top_outer
    )
    set_mock_value(
        mock_locked_apple2.phase().btm_inner.user_readback, initial_phase_top_outer
    )
    set_mock_value(mock_locked_apple2.gap().user_readback, initial_gap)
    assert await mock_apple_knot_i05_controller.polarisation.get_value() == initial_pol
    await mock_apple_knot_i05_controller.energy.set(energy)
    assert await mock_apple_knot_i05_controller.polarisation.get_value() == initial_pol
    assert await mock_apple_knot_i05_controller.energy.get_value() == energy
