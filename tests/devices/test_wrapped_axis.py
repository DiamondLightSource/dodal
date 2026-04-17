import numpy as np
import pytest
from ophyd_async.core import get_mock_put, init_devices, set_mock_value
from ophyd_async.epics.motor import Motor

from dodal.devices.wrapped_axis import WrappedAxis


@pytest.fixture
async def omega() -> Motor:
    async with init_devices(mock=True, connect=True):
        motor = Motor("BL03I-MO-SGON-01:OMEGA")
    return motor


@pytest.fixture
def wrapped_omega(omega: Motor):
    return WrappedAxis(omega, "wrapped_omega")


@pytest.mark.parametrize(
    "initial_unwrapped, phase, expected_omega",
    [
        [0, 0, 0],
        [0, 180, 180],
        [0, 360, 0],
        [180, 360, 0],
        [181, 360, 360],
        [270, 0, 360],
        [-270, 0, -360],
        [0, 450, 90],
    ],
)
async def test_wrapped_axis_set_applies_phase_with_current_set(
    omega: Motor,
    wrapped_omega: WrappedAxis,
    initial_unwrapped: float,
    phase: float,
    expected_omega: float,
):
    set_mock_value(omega.user_readback, initial_unwrapped)
    await wrapped_omega.phase.set(phase)
    get_mock_put(omega.user_setpoint).assert_called_with(expected_omega)


@pytest.mark.parametrize(
    "initial_unwrapped, expected_phase",
    [
        [0, 0],
        [360, 0],
        [-360, 0],
        [90, 90],
        [361, 1],
        [-90, 270],
        [-270, 90],
        [720, 0],
        [450, 90],
    ],
)
async def test_wrapped_axis_get_returns_current_phase(
    omega: Motor,
    wrapped_omega: WrappedAxis,
    initial_unwrapped: float,
    expected_phase: float,
):
    set_mock_value(omega.user_readback, initial_unwrapped)
    phase = await wrapped_omega.phase.get_value()
    assert phase == expected_phase


async def test_wrapped_axis_read_returns_phase_and_offset_phase(
    omega: Motor, wrapped_omega: WrappedAxis
):
    set_mock_value(omega.user_readback, 450)
     await assert_reading(
         wrapped_omega, 
         {
              "wrapped_omega-offset_and_phase": partial_reading(np.array([360, 90]))
              "wrapped_omega-phase": partial_reading(90),
         }
    )


@pytest.mark.parametrize(
    "offset, phase, expected_unwrapped",
    [
        [0, 0, 0],
        [360, 0, 360],
        [-360, 0, -360],
        [0, 90, 90],
        [360, 1, 361],
        [360, -90, 270],
        [0, 270, 270],
        [-360, 90, -270],
        [720, 0, 720],
        [360, 90, 450],
    ],
)
async def test_wrapped_axis_set_offset_and_phase(
    omega: Motor,
    wrapped_omega: WrappedAxis,
    offset: float,
    phase: float,
    expected_unwrapped: float,
):
    await wrapped_omega.offset_and_phase.set(np.array([offset, phase]))
    get_mock_put(omega.user_setpoint).assert_called_once_with(expected_unwrapped)
