from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    get_mock_put,
    partial_reading,
    set_mock_value,
)

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.baton import Baton
from dodal.devices.undulator import (
    AccessError,
    Undulator,
    _get_gap_for_energy,
)
from dodal.testing import patch_all_motors
from tests.devices.test_data import (
    TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT,
)


@pytest.fixture
async def undulator() -> Undulator:
    async with init_devices(mock=True):
        baton = Baton("BATON-01")
        undulator = Undulator(
            "UND-01",
            name="undulator",
            poles=80,
            length=2.0,
            id_gap_lookup_table_path=TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT,
            baton=baton,
        )
    return undulator


@pytest.fixture
def undulator_in_commissioning_mode(
    undulator: Undulator,
) -> Generator[Undulator, None, None]:
    set_mock_value(undulator.baton_ref().commissioning, True)  # type: ignore
    yield undulator


async def test_reading_includes_read_fields(undulator: Undulator):
    await assert_reading(
        undulator,
        {
            "undulator-gap_access": partial_reading(EnabledDisabledUpper.ENABLED),
            "undulator-gap_motor": partial_reading(0.0),
            "undulator-current_gap": partial_reading(0.0),
        },
    )


async def test_configuration_includes_configuration_fields(undulator: Undulator):
    await assert_configuration(
        undulator,
        {
            "undulator-gap_motor-motor_egu": partial_reading(""),
            "undulator-gap_motor-velocity": partial_reading(0.0),
            "undulator-length": partial_reading(2.0),
            "undulator-poles": partial_reading(80),
            "undulator-gap_discrepancy_tolerance_mm": partial_reading(0.002),
            "undulator-gap_motor-offset": partial_reading(0.0),
        },
    )


async def test_poles_not_propagated_if_not_supplied():
    async with init_devices(mock=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            length=2.0,
            id_gap_lookup_table_path=TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT,
        )
    assert undulator.poles is None
    assert "undulator-poles" not in (await undulator.read_configuration())


async def test_length_not_propagated_if_not_supplied():
    async with init_devices(mock=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            poles=80,
            id_gap_lookup_table_path=TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT,
        )
    assert undulator.length is None
    assert "undulator-length" not in (await undulator.read_configuration())


@pytest.mark.parametrize(
    "energy, expected_output",
    [(0, 10), (5, 55), (20, 160), (36, 100), (39, 250)],
)
def test_correct_closest_distance_to_energy_from_table(energy, expected_output):
    energy_to_distance_table = np.array(
        [[0, 10], [10, 100], [35, 250], [35, 50], [40, 300]]
    )
    assert _get_gap_for_energy(energy, energy_to_distance_table) == expected_output


async def test_when_gap_access_is_disabled_set_then_error_is_raised(
    undulator,
):
    set_mock_value(undulator.gap_access, EnabledDisabledUpper.DISABLED)
    with pytest.raises(AccessError):
        await undulator.set(5)


@patch(
    "dodal.devices.undulator.energy_distance_table",
    AsyncMock(return_value=np.array([[0, 10], [10, 20]])),
)
async def test_gap_access_check_disabled_and_move_inhibited_when_commissioning_mode_enabled(
    undulator_in_commissioning_mode: Undulator,
):
    set_mock_value(
        undulator_in_commissioning_mode.gap_access, EnabledDisabledUpper.DISABLED
    )
    await undulator_in_commissioning_mode.set(5)

    get_mock_put(
        undulator_in_commissioning_mode.gap_motor.user_setpoint
    ).assert_not_called()


@patch(
    "dodal.devices.undulator.energy_distance_table",
    AsyncMock(return_value=np.array([[0, 10], [10000, 20]])),
)
async def test_gap_access_check_move_not_inhibited_when_commissioning_mode_disabled(
    undulator: Undulator,
):
    with patch_all_motors(undulator):
        set_mock_value(undulator.gap_access, EnabledDisabledUpper.ENABLED)
        await undulator.set(5)

        get_mock_put(undulator.gap_motor.user_setpoint).assert_called_once_with(
            15.0, wait=True
        )
