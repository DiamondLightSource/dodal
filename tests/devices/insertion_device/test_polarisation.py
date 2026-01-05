from unittest.mock import AsyncMock, MagicMock

import pytest
from bluesky.protocols import Location
from ophyd_async.core import StrictEnum, init_devices

from dodal.devices.insertion_device import (
    MAXIMUM_MOVE_TIME,
    Apple2,
    Apple2Controller,
    Apple2PhasesVal,
    Apple2Val,
    InsertionDevicePolarisation,
    Pol,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import EnergyMotorLookup
from dodal.devices.pgm import PlaneGratingMonochromator

pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


class DummyApple2Controller(Apple2Controller[Apple2[UndulatorPhaseAxes]]):
    """
    I10Apple2Controller is a extension of Apple2Controller which provide linear
    arbitrary angle control.
    """

    def __init__(
        self,
        apple2: Apple2[UndulatorPhaseAxes],
        gap_energy_motor_lut: EnergyMotorLookup,
        phase_energy_motor_lut: EnergyMotorLookup,
        units: str = "eV",
        name: str = "",
    ) -> None:
        self.gap_energy_motor_lut = gap_energy_motor_lut
        self.phase_energy_motor_lut = phase_energy_motor_lut
        super().__init__(
            apple2=apple2,
            gap_energy_motor_converter=gap_energy_motor_lut.find_value_in_lookup_table,
            phase_energy_motor_converter=phase_energy_motor_lut.find_value_in_lookup_table,
            units=units,
            name=name,
        )

    def _get_apple2_value(self, gap: float, phase: float, pol: Pol) -> Apple2Val:
        return Apple2Val(
            gap=gap,
            phase=Apple2PhasesVal(
                top_outer=phase,
                top_inner=0.0,
                btm_inner=phase,
                btm_outer=0.0,
            ),
        )


class Grating(StrictEnum):
    AU_400 = "400 line/mm Au"
    SI_400 = "400 line/mm Si"
    AU_1200 = "1200 line/mm Au"


@pytest.fixture
async def mock_pgm(prefix: str = "BLXX-EA-DET-007:") -> PlaneGratingMonochromator:
    async with init_devices(mock=True):
        mock_pgm = PlaneGratingMonochromator(
            prefix=prefix, grating=Grating, grating_pv="NLINES2"
        )
    return mock_pgm


@pytest.fixture
async def mock_apple2(
    mock_id_gap: UndulatorGap, mock_phase_axes: UndulatorPhaseAxes
) -> Apple2:
    async with init_devices(mock=True):
        mock_apple2 = Apple2(id_gap=mock_id_gap, id_phase=mock_phase_axes)
    return mock_apple2


@pytest.fixture
async def mock_id_controller(
    mock_apple2: Apple2[UndulatorPhaseAxes],
) -> DummyApple2Controller:
    mock_gap_energy_motor_lut = EnergyMotorLookup()
    mock_gap_energy_motor_lut.find_value_in_lookup_table = MagicMock(return_value=42.0)
    mock_phase_energy_motor_lut = EnergyMotorLookup()
    mock_phase_energy_motor_lut.find_value_in_lookup_table = MagicMock(return_value=7.5)
    with init_devices(mock=True):
        mock_id_controller = DummyApple2Controller(
            apple2=mock_apple2,
            gap_energy_motor_lut=mock_gap_energy_motor_lut,
            phase_energy_motor_lut=mock_phase_energy_motor_lut,
        )
    return mock_id_controller


@pytest.fixture
async def mock_id_polarisation(
    mock_id_controller: DummyApple2Controller,
) -> InsertionDevicePolarisation:
    async with init_devices(mock=True):
        mock_id_polarisation = InsertionDevicePolarisation(
            id_controller=mock_id_controller,
        )
    return mock_id_polarisation


async def test_polarisation_set_calls_controller_methods(
    mock_id_controller: DummyApple2Controller,
    mock_id_polarisation: InsertionDevicePolarisation,
):
    mock_id_controller.polarisation.set = AsyncMock()
    pol = Pol.PC
    await mock_id_polarisation.set(pol=pol)
    mock_id_controller.polarisation.set.assert_called_once_with(
        pol, timeout=MAXIMUM_MOVE_TIME
    )


async def test_insertion_device_polarisation_locate(
    mock_id_controller: DummyApple2Controller,
    mock_id_polarisation: InsertionDevicePolarisation,
):
    pol = Pol.LH
    mock_id_controller.polarisation_setpoint.get_value = AsyncMock(return_value=pol)
    mock_id_controller.polarisation.get_value = AsyncMock(return_value=pol)
    location = await mock_id_polarisation.locate()
    assert location == Location(setpoint=pol, readback=pol)
