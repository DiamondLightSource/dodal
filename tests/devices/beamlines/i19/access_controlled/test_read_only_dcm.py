import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i19.access_controlled.read_only_dcm import ReadOnlyDCM


@pytest.fixture
async def mock_dcm() -> ReadOnlyDCM:
    mock_dcm = ReadOnlyDCM(prefix="FOO-MO")
    await mock_dcm.connect(mock=True)
    set_mock_value(mock_dcm.energy_in_eV, 1)
    set_mock_value(mock_dcm.wavelength_in_a, 100)
    return mock_dcm


async def test_reading(mock_dcm: ReadOnlyDCM, run_engine: RunEngine):
    prefix = "FOO-MO"
    await assert_reading(
        mock_dcm,
        {
            f"{prefix}-energy_in_eV": partial_reading(1.0),
            f"{prefix}-wavelength_in_a": partial_reading(100.0),
        },
        False,
    )
