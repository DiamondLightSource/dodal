from unittest.mock import MagicMock

import pytest
from ophyd_async.core import init_devices

from dodal.devices.apple2_undulator import (
    Apple2,
    InsertionDeviceEnergy,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.k07 import K07Apple2Controller


@pytest.fixture
async def id_gap() -> UndulatorGap:
    async with init_devices(mock=True):
        return UndulatorGap(prefix="TEST-MO-SERVC-01:")


@pytest.fixture
async def id_phase() -> UndulatorPhaseAxes:
    async with init_devices(mock=True):
        return UndulatorPhaseAxes(
            prefix="TEST-MO-SERVC-01:",
            top_outer="RPQ1",
            top_inner="RPQ2",
            btm_inner="RPQ3",
            btm_outer="RPQ4",
        )


@pytest.fixture
async def id(
    id_gap: UndulatorGap,
    id_phase: UndulatorPhaseAxes,
) -> Apple2:
    async with init_devices(mock=True):
        return Apple2(id_gap=id_gap, id_phase=id_phase)


@pytest.fixture
async def id_controller(id: Apple2) -> K07Apple2Controller:
    async with init_devices(mock=True):
        return K07Apple2Controller(apple2=id)


# Insertion device controller does not exist yet - this class is a placeholder for when it does
async def test_id_controller_set_energy(id_controller: K07Apple2Controller) -> None:
    async with init_devices(mock=True):
        id_energy = InsertionDeviceEnergy(id_controller=id_controller)
    assert id_energy is not None
    id_controller._set_motors_from_energy = MagicMock(
        side_effect=id_controller._set_motors_from_energy
    )
    await id_energy.set(500.0)
    id_controller._set_motors_from_energy.assert_called_once_with(500.0)
    assert await id_controller.energy.get_value() == 500.0
