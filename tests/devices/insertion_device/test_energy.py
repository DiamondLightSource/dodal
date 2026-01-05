from unittest.mock import AsyncMock, MagicMock

import pytest
from ophyd_async.core import StrictEnum, init_devices

from dodal.devices.insertion_device import (
    MAXIMUM_MOVE_TIME,
    Apple2,
    Apple2Controller,
    Apple2PhasesVal,
    Apple2Val,
    BeamEnergy,
    InsertionDeviceEnergy,
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
async def mock_id_energy(
    mock_id_controller: DummyApple2Controller,
) -> InsertionDeviceEnergy:
    async with init_devices(mock=True):
        mock_id_energy = InsertionDeviceEnergy(
            id_controller=mock_id_controller,
        )

    return mock_id_energy


@pytest.fixture
async def beam_energy(
    mock_id_energy: InsertionDeviceEnergy, mock_pgm: PlaneGratingMonochromator
) -> BeamEnergy:
    async with init_devices(mock=True):
        beam_energy = BeamEnergy(id_energy=mock_id_energy, mono=mock_pgm.energy)
    return beam_energy


@pytest.fixture
async def mock_id_pol(
    mock_id_controller: DummyApple2Controller,
) -> InsertionDevicePolarisation:
    async with init_devices(mock=True):
        mock_id_pol = InsertionDevicePolarisation(id_controller=mock_id_controller)

    return mock_id_pol


async def test_beam_energy_set_moves_both_devices(
    beam_energy: BeamEnergy,
    mock_id_energy: InsertionDeviceEnergy,
    mock_pgm: PlaneGratingMonochromator,
):
    mock_id_energy.set = AsyncMock()
    mock_pgm.energy.set = AsyncMock()

    await beam_energy.set(100.0)

    mock_id_energy.set.assert_called_once_with(energy=100.0)
    mock_pgm.energy.set.assert_called_once_with(100.0)


async def test_insertion_device_energy_set(
    mock_id_energy: InsertionDeviceEnergy,
    mock_id_controller: DummyApple2Controller,
):
    mock_id_controller.energy.set = AsyncMock()

    await mock_id_energy.set(1500.0)

    mock_id_controller.energy.set.assert_awaited_once_with(
        1500.0, timeout=MAXIMUM_MOVE_TIME
    )
