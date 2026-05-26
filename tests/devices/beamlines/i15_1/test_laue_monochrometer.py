import pytest
from daq_config_server import ConfigClient
from daq_config_server.models.i15_1 import XpdfCrystalLookupTable
from ophyd_async.core import get_mock_put, init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i15_1.laue import LaueMonochrometer
from tests.test_data import TEST_I15_1_CRYSTAL_LUT


@pytest.fixture
def laue_monochrometer():
    with init_devices(mock=True):
        monocrometer = LaueMonochrometer(
            prefix="",
            config_client=ConfigClient(""),
            crystal_lut_path=TEST_I15_1_CRYSTAL_LUT,
        )
    return monocrometer


def test__get_xtal_config_returns_expected_configuration(
    laue_monochrometer: LaueMonochrometer,
):
    config = laue_monochrometer._get_xtal_config()
    assert config == XpdfCrystalLookupTable(
        rows=[[1.455, 40.05], [-48.845, 65.4], [50.6, 76.69]]
    )


@pytest.mark.parametrize(
    "y, expected_energy",
    [
        (1.455, 40.05),
        (1.56, 40.05),
        (50, 76.69),
        (50.6, 76.69),
        (-48.845, 65.4),
        (-50, 65.4),
    ],
)
async def test_energy_kev_gets_value_based_on_y(
    laue_monochrometer: LaueMonochrometer, y, expected_energy
):
    await laue_monochrometer.y.set(y)
    assert await laue_monochrometer.energy_kev.get_value() == expected_energy
    await assert_reading(
        laue_monochrometer,
        {f"{laue_monochrometer.name}-energy_kev": partial_reading(expected_energy)},
        full_match=False,
    )


@pytest.mark.parametrize(
    "energy, expected_y",
    [(40.05, 1.455), (76.69, 50.6), (65.4, -48.845)],
)
async def test_setting_energy_moves_y_to_expected_value(
    laue_monochrometer: LaueMonochrometer, energy, expected_y
):
    await laue_monochrometer.energy_kev.set(energy)
    get_mock_put(laue_monochrometer.y.user_setpoint).assert_called_once_with(expected_y)


async def test_setting_energy_with_invalid_energy_raises_error(
    laue_monochrometer: LaueMonochrometer,
):
    with pytest.raises(ValueError):
        await laue_monochrometer.energy_kev.set(10)
