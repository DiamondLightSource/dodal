import pytest
from ophyd_async.core import set_mock_value

from dodal.devices.beamlines.i19.access_controlled.read_only_dcm import ReadOnlyDCM


@pytest.fixture
async def mock_dcm() -> ReadOnlyDCM:
    mock_dcm = ReadOnlyDCM(prefix="FOO-MO")
    await mock_dcm.connect(mock=True)
    set_mock_value(mock_dcm.energy_in_eV, 1)
    set_mock_value(mock_dcm.wavelength_in_a, 100)
    return mock_dcm


async def test_reading(mock_dcm: ReadOnlyDCM):
    assert await mock_dcm.energy_in_eV.get_value() == 1
    assert await mock_dcm.wavelength_in_a.get_value() == 100
