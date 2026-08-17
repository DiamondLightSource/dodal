import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from ophyd_async.core import AsyncStatus, init_devices, set_mock_value

from dodal.devices.insertion_device import Pol
from dodal.devices.insertion_device.energy_motor_lookup import (
    ConfigServerEnergyMotorLookup,
    EnergyCoverage,
    EnergyMotorLookup,
    EpicsPolynomialEnergyMotorLookup,
    StaticPolynomialEnergyMotorLookup,
)
from dodal.devices.insertion_device.lookup_table_models import (
    MAXIMUM_ROW_PHASE_MOTOR_POSITION,
    LookupTable,
)
from tests.devices.insertion_device.util import (
    GenerateConfigLookupTable,
    assert_expected_lut_equals_energy_motor_update_after_update,
)


@pytest.fixture
def energy_motor_lookup(lut: LookupTable) -> EnergyMotorLookup:
    return EnergyMotorLookup(lut)


def test_energy_motor_lookup_find_value_in_lookup_table(
    energy_motor_lookup: EnergyMotorLookup,
    generate_config_lut: GenerateConfigLookupTable,
) -> None:
    for i in range(len(generate_config_lut.polarisations)):
        energy = generate_config_lut.energy_coverage[i].min_energy
        value = energy_motor_lookup.find_value_in_lookup_table(
            value=energy,
            pol=generate_config_lut.polarisations[i],
        )
        expected_poly = generate_config_lut.energy_coverage[i].get_poly(energy)
        expected_value = expected_poly(energy)
        assert value == expected_value


def test_energy_motor_lookup_update_is_static(
    energy_motor_lookup: EnergyMotorLookup,
) -> None:
    before_update_lut = energy_motor_lookup.lut
    assert_expected_lut_equals_energy_motor_update_after_update(
        before_update_lut, energy_motor_lookup
    )


def test_energy_motor_lookup_find_value_in_lookup_table_updates_lut_if_lut_empty(
    energy_motor_lookup: EnergyMotorLookup,
    generate_config_lut: GenerateConfigLookupTable,
) -> None:
    energy = 100
    pol = Pol.LH

    mock_lut = MagicMock(wraps=LookupTable())
    # Set the lut data to empty to force an update
    mock_lut.root = {}
    mock_lut.get_poly.return_value = generate_config_lut.energy_coverage[0].get_poly(
        energy
    )

    # Replace methods and data with mocks
    energy_motor_lookup.lut = mock_lut
    mock_update_lut = MagicMock()
    energy_motor_lookup.update_lookup_table = mock_update_lut

    energy_motor_lookup.find_value_in_lookup_table(energy, pol)
    mock_update_lut.assert_called_once()
    mock_lut.get_poly.assert_called_once_with(value=energy, pol=pol)


@pytest.fixture
def config_server_energy_motor_lookup() -> ConfigServerEnergyMotorLookup:
    return ConfigServerEnergyMotorLookup(MagicMock(), MagicMock(), Path("dummy_path"))


def test_config_server_energy_motor_lookup_update_lookup_table(
    config_server_energy_motor_lookup: ConfigServerEnergyMotorLookup,
    lut: LookupTable,
) -> None:
    assert config_server_energy_motor_lookup.lut == LookupTable()
    mock_read_lut = MagicMock(return_value=lut)
    config_server_energy_motor_lookup.read_lut = mock_read_lut

    config_server_energy_motor_lookup.find_value_in_lookup_table(100, Pol.LH)
    mock_read_lut.assert_called_once()
    assert config_server_energy_motor_lookup.lut == lut


ROW_PHASE_CIRCULAR = 15.0
DEFAULT_POLY1D_PARAMETERS = {
    Pol.LH: [0],
    Pol.LV: [MAXIMUM_ROW_PHASE_MOTOR_POSITION],
    Pol.PC: [ROW_PHASE_CIRCULAR],
    Pol.PC3: [ROW_PHASE_CIRCULAR],
    Pol.NC: [-ROW_PHASE_CIRCULAR],
    Pol.NC3: [-ROW_PHASE_CIRCULAR],
}


@pytest.fixture
async def polynomial_device() -> StaticPolynomialEnergyMotorLookup:
    async with init_devices(mock=True):
        poly_device = StaticPolynomialEnergyMotorLookup(
            max_value=2200,
            min_value=70,
            poly_params=DEFAULT_POLY1D_PARAMETERS,
        )
    return poly_device


@pytest.mark.parametrize(
    "param_dict",
    [
        {Pol.LH: [1.0, 2.0, 3.0], Pol.PC: [1.0, 2.0, 3.0]},
    ],
)
async def test_static_polynomial_device_get_table_entries_list(
    param_dict: dict[Pol, list[float]],
    polynomial_device: StaticPolynomialEnergyMotorLookup,
) -> None:

    entries = polynomial_device._generate_entries(param_dict=param_dict)
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


@pytest.fixture
async def epics_polynomial_device() -> EpicsPolynomialEnergyMotorLookup:
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
        {Pol.LH: [1.0, 5.0, 2.0], Pol.PC: [1.0, 2.0, 3.0]},
    ],
)
async def test_epics_polynomial_device_get_table_entries_deviceector(
    param_dict: dict[Pol, list[float]],
    epics_polynomial_device: EpicsPolynomialEnergyMotorLookup,
) -> None:
    for pol, coeffs in param_dict.items():
        for i, coeff in enumerate(coeffs):
            set_mock_value(
                epics_polynomial_device.param_dict[pol][i + 1],
                coeff,
            )
    await epics_polynomial_device.update_lookup()
    entries = epics_polynomial_device.lut.root
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
    epics_polynomial_device: EpicsPolynomialEnergyMotorLookup,
) -> None:
    param_dict = {
        Pol.LH: [1.0, 5.0, 2.0],
        Pol.PC: [1.0, 2.0, 3.0],
    }
    for pol, coeffs in param_dict.items():
        for i, coeff in enumerate(coeffs):
            set_mock_value(
                epics_polynomial_device.param_dict[pol][i + 1],
                coeff,
            )

    await epics_polynomial_device.update_lookup()
    np.testing.assert_allclose(
        epics_polynomial_device.lut.root[Pol.LH].energy_entries[0].poly.coefficients,
        np.array([2.0, 5.0, 1.0]),
    )
    np.testing.assert_allclose(
        epics_polynomial_device.lut.root[Pol.PC].energy_entries[0].poly.coefficients,
        np.array([3.0, 2.0, 1.0]),
    )


async def test_update_lookup_logs_and_raises_on_error(
    epics_polynomial_device: EpicsPolynomialEnergyMotorLookup,
    caplog: pytest.LogCaptureFixture,
):

    for vector in epics_polynomial_device.param_dict.values():
        for signal in vector.values():
            signal.get_value = AsyncMock(side_effect=RuntimeError("EPICS Disconnected"))

    with pytest.raises(RuntimeError, match="EPICS Disconnected"):
        await epics_polynomial_device.update_lookup()

    assert (
        f"Failed to update {epics_polynomial_device.name}: EPICS Disconnected"
        in caplog.text
    )


def test_update_lookup_table(
    epics_polynomial_device: EpicsPolynomialEnergyMotorLookup,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        epics_polynomial_device.update_lookup_table()
        assert (
            f"Synchronous update_lookup_table called on {epics_polynomial_device.name}"
            in caplog.text
        )
