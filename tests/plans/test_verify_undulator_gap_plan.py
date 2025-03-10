from unittest.mock import AsyncMock, patch

from bluesky.run_engine import RunEngine
from ophyd_async.testing import set_mock_value
from tests.plans.conftest import UndulatorGapCheckDevices

from dodal.plans.verify_undulator_gap import verify_undulator_gap


@patch("dodal.devices.undulator.Undulator._set_undulator_gap", new_callable=AsyncMock)
def test_verify_undulator_gap(
    mock_set: AsyncMock, mock_undulator_and_dcm: UndulatorGapCheckDevices, RE: RunEngine
):
    kev_val = 5
    set_mock_value(mock_undulator_and_dcm.dcm.energy_in_kev.user_readback, kev_val)
    RE(verify_undulator_gap(mock_undulator_and_dcm))
    mock_set.assert_called_once_with(kev_val)
