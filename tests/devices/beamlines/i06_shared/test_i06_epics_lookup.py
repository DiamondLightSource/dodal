from unittest.mock import AsyncMock, patch

import numpy as np
import pytest
from ophyd_async.core import AsyncStatus, init_devices, set_mock_value

from dodal.devices.beamlines.i06_shared import (
    EpicsPolynomialEnergyMotorLookup,
    I06EpicsPolynomialDevice,
)
from dodal.devices.insertion_device import Pol
from dodal.devices.insertion_device.lookup_table_models import EnergyCoverage


@pytest.fixture
async def epics_polynomial_device() -> EpicsPolynomialEnergyMotorLookup:
    async with init_devices(mock=True):
        poly_device = EpicsPolynomialEnergyMotorLookup(
            prefix="TEST",
            max_value=2200,
            min_value=70,
        )
    return poly_device


@pytest.fixture
async def epics_polynomial_device_vectors() -> EpicsPolynomialEnergyMotorLookup:
    async with init_devices(mock=True):
        poly_device = EpicsPolynomialEnergyMotorLookup(
            prefix="TEST",
            max_value=2200,
            min_value=70,
            poly_params={
                Pol.LH: "HZ",
                Pol.LV: "VT",
                Pol.PC: "PC",
                Pol.NC: "NC",
                Pol.PC3: "PC:HAR3",
                Pol.NC3: "NC:HAR3",
            },
        )
    return poly_device


async def test_epics_polynomial_device_connection(
    epics_polynomial_device: EpicsPolynomialEnergyMotorLookup,
) -> None:
    epics_polynomial_device.update_lookup = AsyncMock()
    with patch("ophyd_async.core.Device.connect") as mock_connect:
        await epics_polynomial_device.connect()
        mock_connect.assert_awaited_once()
        epics_polynomial_device.update_lookup.assert_awaited_once()


async def test_epics_polynomial_device_trigger(
    epics_polynomial_device: EpicsPolynomialEnergyMotorLookup,
) -> None:
    epics_polynomial_device.update_lookup = AsyncMock()
    status = epics_polynomial_device.trigger()
    assert isinstance(status, AsyncStatus)
    assert not status.done
    await status
    assert status.done
    epics_polynomial_device.update_lookup.assert_awaited_once()


@pytest.mark.parametrize(
    "param_dict",
    [
        {Pol.LH: [1.0, 2.0, 3.0], Pol.PC: [1.0, 2.0, 3.0]},
    ],
)
async def test_epics_polynomial_device_get_table_entries_list(
    param_dict: dict[Pol, list[float]],
    epics_polynomial_device: EpicsPolynomialEnergyMotorLookup,
) -> None:

    entries = await epics_polynomial_device._get_table_entries(
        param_dict=param_dict,
        min_value=70,
        max_value=2200,
    )
    energy = 100
    assert Pol.LH in entries
    assert Pol.PC in entries
    assert isinstance(entries[Pol.LH], EnergyCoverage)
    assert isinstance(entries[Pol.PC], EnergyCoverage)
    assert entries[Pol.LH].get_poly(energy)(energy) == pytest.approx(
        np.poly1d(param_dict[Pol.LH])(energy),
        rel=0.01,
    )
    assert entries[Pol.PC].get_poly(energy)(energy) == pytest.approx(
        np.poly1d(param_dict[Pol.PC])(energy),
        rel=0.01,
    )


@pytest.mark.parametrize(
    "param_dict",
    [
        {Pol.LH: [1.0, 5.0, 2.0], Pol.PC: [1.0, 2.0, 3.0]},
    ],
)
async def test_epics_polynomial_device_get_table_entries_deviceector(
    param_dict: dict[Pol, list[float]],
    epics_polynomial_device_vectors: EpicsPolynomialEnergyMotorLookup,
) -> None:
    for pol, coeffs in param_dict.items():
        for i, coeff in enumerate(coeffs):
            set_mock_value(
                epics_polynomial_device_vectors.param_dict[pol][i + 1],
                coeff,
            )
    entries = await epics_polynomial_device_vectors._get_table_entries(
        param_dict=epics_polynomial_device_vectors.param_dict,
        min_value=70,
        max_value=2200,
    )
    energy = 100
    assert Pol.LH in entries
    assert Pol.PC in entries
    assert isinstance(entries[Pol.LH], EnergyCoverage)
    assert isinstance(entries[Pol.PC], EnergyCoverage)
    assert entries[Pol.LH].get_poly(energy)(energy) == pytest.approx(
        np.poly1d(list(reversed(param_dict[Pol.LH])))(energy),
        rel=0.01,
    )
    assert entries[Pol.PC].get_poly(energy)(energy) == pytest.approx(
        np.poly1d(list(reversed(param_dict[Pol.PC])))(energy),
        rel=0.01,
    )


async def test_epics_polynomial_device_update_lookup(
    epics_polynomial_device_vectors: EpicsPolynomialEnergyMotorLookup,
) -> None:
    param_dict = {
        Pol.LH: [1.0, 5.0, 2.0],
        Pol.PC: [1.0, 2.0, 3.0],
    }
    for pol, coeffs in param_dict.items():
        for i, coeff in enumerate(coeffs):
            set_mock_value(
                epics_polynomial_device_vectors.param_dict[pol][i + 1],
                coeff,
            )

    await epics_polynomial_device_vectors.update_lookup()
    np.testing.assert_allclose(
        epics_polynomial_device_vectors.lut.root[Pol.LH]
        .energy_entries[0]
        .poly.coefficients,
        np.array([2.0, 5.0, 1.0]),
    )
    np.testing.assert_allclose(
        epics_polynomial_device_vectors.lut.root[Pol.PC]
        .energy_entries[0]
        .poly.coefficients,
        np.array([3.0, 2.0, 1.0]),
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
