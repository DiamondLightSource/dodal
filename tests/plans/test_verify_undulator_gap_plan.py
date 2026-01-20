from unittest.mock import AsyncMock, patch

from bluesky.run_engine import RunEngine
from ophyd_async.core import set_mock_value

from dodal.plans.verify_undulator_gap import verify_undulator_gap
from tests.plans.conftest import UndulatorGapCheckDevices


@patch("dodal.devices.undulator.BaseUndulator._set_gap", new_callable=AsyncMock)
def test_verify_undulator_gap(
    mock_set: AsyncMock,
    mock_undulator_and_dcm: UndulatorGapCheckDevices,
    run_engine: RunEngine,
):
    kev_val = 5
    expected_gap = 5.4606
    set_mock_value(mock_undulator_and_dcm.dcm.energy_in_keV.user_readback, kev_val)
    run_engine(verify_undulator_gap(mock_undulator_and_dcm))
    mock_set.assert_called_once_with(expected_gap)
