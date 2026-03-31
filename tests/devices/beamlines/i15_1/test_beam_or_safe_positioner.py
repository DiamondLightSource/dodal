import pytest
from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import TemperatureControllerParams
from ophyd_async.core import get_mock_put, init_devices, set_mock_value

from dodal.devices.beamlines.i15_1.temperature_controller import (
    SafeOrBeamPosition,
    SafeOrBeamPositioner,
)

BEAM_POSITION = 100.0
SAFE_POSITION = 2.0


@pytest.fixture
async def positioner() -> SafeOrBeamPositioner:
    class MockSafeOrBeamPositioner(SafeOrBeamPositioner):
        def get_config(self) -> TemperatureControllerParams:
            return TemperatureControllerParams(
                beam_position=BEAM_POSITION,
                safe_position=SAFE_POSITION,
                settle_time=0,
                tolerance=5.0,
                units="C",
                ramp_units="/min",
                use_calibration=True,
                use_fast_cool=None,
                calibration_file="",
            )

    async with init_devices(mock=True):
        mock_positioner = MockSafeOrBeamPositioner("", ConfigClient(""), "")

    set_mock_value(mock_positioner.motor.user_readback, 50.0)
    return mock_positioner


def test_positioner_gets_safe_and_beam_values_from_config(
    positioner: SafeOrBeamPositioner,
):
    assert positioner.get_config().safe_position == SAFE_POSITION
    assert positioner._safe_position == SAFE_POSITION
    assert positioner.get_config().beam_position == BEAM_POSITION
    assert positioner._beam_position == BEAM_POSITION


async def test_positioner_moves_to_safe_value_when_set(
    positioner: SafeOrBeamPositioner,
):
    await positioner.set(SafeOrBeamPosition.SAFE)
    get_mock_put(positioner.motor.user_setpoint).assert_called_once_with(SAFE_POSITION)


async def test_positioner_moves_to_beam_value_when_set(
    positioner: SafeOrBeamPositioner,
):
    await positioner.set(SafeOrBeamPosition.BEAM)
    get_mock_put(positioner.motor.user_setpoint).assert_called_once_with(BEAM_POSITION)
