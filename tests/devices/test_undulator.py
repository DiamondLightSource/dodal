from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest
from bluesky import RunEngine
from bluesky.plan_stubs import mv
from ophyd_async.core import get_mock_put, init_devices, set_mock_value
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    partial_reading,
)

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.baton import Baton
from dodal.devices.undulator import (
    AccessError,
    UndulatorInKeV,
    UndulatorInMm,
    UndulatorOrder,
    _get_gap_for_energy,
)
from tests.devices.test_data import (
    TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT,
)

LUT_DICT = {1: [0.0, 1.0], 2: [0.4, 0.3], 3: [1.0, 4.9]}


@pytest.fixture
async def undulator() -> UndulatorInKeV:
    async with init_devices(mock=True):
        baton = Baton("BATON-01")
        undulator = UndulatorInKeV(
            "UND-01",
            name="undulator",
            poles=80,
            length=2.0,
            undulator_period=27,
            id_gap_lookup_table_path=TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT,
            baton=baton,
        )
    return undulator


@pytest.fixture
async def undulator_in_mm() -> UndulatorInMm:
    async with init_devices(mock=True):
        baton = Baton("BATON-01")
        undulator_mm = UndulatorInMm(
            "UND-02",
            baton=baton,
        )
    return undulator_mm


@pytest.fixture
def undulator_in_commissioning_mode(
    undulator: UndulatorInKeV,
) -> Generator[UndulatorInKeV, None, None]:
    set_mock_value(undulator.baton_ref().commissioning, True)  # type: ignore
    yield undulator


async def test_undulator_mm_config_default_parameters(undulator_in_mm: UndulatorInMm):
    await assert_configuration(
        undulator_in_mm,
        {
            "undulator_mm-gap_discrepancy_tolerance_mm": partial_reading(0.002),
            "undulator_mm-gap_motor-motor_egu": partial_reading(""),
            "undulator_mm-gap_motor-offset": partial_reading(0.0),
            "undulator_mm-gap_motor-velocity": partial_reading(1000.0),
        },
    )


@pytest.fixture
async def undulator_order() -> UndulatorOrder:
    async with init_devices(mock=True):
        order = UndulatorOrder(name="undulator_order")
    return order


async def test_reading_includes_read_fields(undulator: UndulatorInKeV):
    await assert_reading(
        undulator,
        {
            "undulator-gap_access": partial_reading(EnabledDisabledUpper.ENABLED),
            "undulator-gap_motor": partial_reading(0.0),
            "undulator-current_gap": partial_reading(0.0),
        },
    )


async def test_configuration_includes_configuration_fields(undulator: UndulatorInKeV):
    await assert_configuration(
        undulator,
        {
            "undulator-gap_motor-motor_egu": partial_reading(""),
            "undulator-gap_motor-velocity": partial_reading(1000.0),
            "undulator-length": partial_reading(2.0),
            "undulator-poles": partial_reading(80),
            "undulator-gap_discrepancy_tolerance_mm": partial_reading(0.002),
            "undulator-gap_motor-offset": partial_reading(0.0),
            "undulator-undulator_period": partial_reading(27),
        },
    )


async def test_poles_not_propagated_if_not_supplied():
    async with init_devices(mock=True):
        undulator = UndulatorInKeV(
            "UND-01",
            name="undulator",
            length=2.0,
            id_gap_lookup_table_path=TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT,
        )
    assert undulator.poles is None
    assert "undulator-poles" not in (await undulator.read_configuration())


async def test_length_not_propagated_if_not_supplied():
    async with init_devices(mock=True):
        undulator = UndulatorInKeV(
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
    undulator_in_commissioning_mode: UndulatorInKeV,
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
    undulator: UndulatorInKeV,
):
    set_mock_value(undulator.gap_access, EnabledDisabledUpper.ENABLED)
    await undulator.set(5)

    get_mock_put(undulator.gap_motor.user_setpoint).assert_called_once_with(
        15.0, wait=True
    )


async def test_undulator_mm_move(undulator_in_mm: UndulatorInMm):
    await undulator_in_mm.set(10.0)
    get_mock_put(undulator_in_mm.gap_motor.user_setpoint).assert_called_once_with(
        10.0, wait=True
    )


async def test_order_read(
    undulator_order: UndulatorOrder,
):
    await assert_reading(
        undulator_order,
        {"undulator_order-value": partial_reading(3)},
    )


async def test_move_order(
    undulator_order: UndulatorOrder,
    run_engine: RunEngine,
):
    assert await undulator_order.value.get_value() == 3  # default order
    run_engine(mv(undulator_order, 1))
    assert await undulator_order.value.get_value() == 1  # no error


@pytest.mark.parametrize(
    "order_value",
    [-1, 1.56],
)
async def test_move_order_fails(
    undulator_order: UndulatorOrder,
    order_value: float | int,
):
    with pytest.raises(
        ValueError,
        match=f"Undulator order must be a positive integer. Requested value: {order_value}",
    ):
        await undulator_order.set(order_value)  # type: ignore


async def test_locate_undulator_order(
    undulator_order: UndulatorOrder,
    order_value: int = 3,
):
    await undulator_order.set(order_value)
    located_position = await undulator_order.locate()
    assert located_position == {"readback": order_value, "setpoint": order_value}
