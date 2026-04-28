from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import AsyncStatus, init_devices

from dodal.devices.beamlines.i06_shared import (
    I06EpicsPolynomialDevice,
)


@pytest.fixture
async def i06_epics_polynomial_device() -> I06EpicsPolynomialDevice:
    async with init_devices(mock=True):
        poly_device = I06EpicsPolynomialDevice(prefix="TEST", name="poly_device")
    return poly_device


async def test_i06_epics_polynomial_device_trigger(
    i06_epics_polynomial_device: I06EpicsPolynomialDevice,
) -> None:
    i06_epics_polynomial_device.energy_gap_motor_lookup.update_lookup = AsyncMock()
    i06_epics_polynomial_device.energy_phase_motor_lookup.update_lookup = AsyncMock()
    i06_epics_polynomial_device.gap_motor_energy_lookup.update_lookup = AsyncMock()
    status = i06_epics_polynomial_device.trigger()
    assert isinstance(status, AsyncStatus)
    assert not status.done
    await status
    assert status.done
    i06_epics_polynomial_device.energy_gap_motor_lookup.update_lookup.assert_awaited_once()
    i06_epics_polynomial_device.energy_phase_motor_lookup.update_lookup.assert_awaited_once()
    i06_epics_polynomial_device.gap_motor_energy_lookup.update_lookup.assert_awaited_once()
