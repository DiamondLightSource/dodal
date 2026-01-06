from unittest.mock import MagicMock

import pytest
from ophyd_async.core import StrictEnum, init_devices
from pytest import FixtureRequest

from dodal.devices.insertion_device import (
    Apple2,
    Apple2Controller,
    Apple2PhasesVal,
    Apple2Val,
    EnergyCoverage,
    InsertionDeviceEnergy,
    LookupTable,
    Pol,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import EnergyMotorLookup
from dodal.devices.pgm import PlaneGratingMonochromator
from tests.devices.insertion_device.util import GenerateConfigLookupTable


@pytest.fixture(
    params=[
        # Single polarisation entry with multiple energy coverage entries e.g i10
        GenerateConfigLookupTable(
            polarisations=[Pol.LH],
            energy_coverage=[
                EnergyCoverage.generate(
                    min_energies=[100, 200],
                    max_energies=[200, 250],
                    poly1d_params=[[2.0, -1.0, 0.5], [1.0, 0.0]],
                )
            ],
        ),
        # Mutiple polarisation entries with single energy coverage entry e.g i09
        GenerateConfigLookupTable(
            polarisations=[Pol.LH, Pol.LV],
            energy_coverage=[
                EnergyCoverage.generate(
                    min_energies=[100], max_energies=[150], poly1d_params=[[1.0, 0.0]]
                ),
                EnergyCoverage.generate(
                    min_energies=[200], max_energies=[250], poly1d_params=[[0.5, 1.0]]
                ),
            ],
        ),
    ]
)
def generate_config_lut(request: FixtureRequest) -> GenerateConfigLookupTable:
    return request.param


@pytest.fixture
def lut(generate_config_lut: GenerateConfigLookupTable) -> LookupTable:
    return LookupTable.generate(
        pols=generate_config_lut.polarisations,
        energy_coverage=generate_config_lut.energy_coverage,
    )


class DummyApple2Controller(Apple2Controller[Apple2[UndulatorPhaseAxes]]):
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
