import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.epics.motor import Motor
from ophyd_async.sim import SimMotor
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.beamlines.i05 import PolynomCompoundMotors


@pytest.fixture
async def x_motor() -> SimMotor:
    async with init_devices(mock=True):
        x_motor = SimMotor()
    return x_motor


@pytest.fixture
async def y_motor() -> SimMotor:
    async with init_devices(mock=True):
        y_motor = SimMotor()
    return y_motor


@pytest.fixture
async def z_motor() -> SimMotor:
    async with init_devices(mock=True):
        z_motor = SimMotor()
    return z_motor


@pytest.fixture
async def mock_compound(
    x_motor: Motor,
    y_motor: Motor,
    z_motor: Motor,
) -> PolynomCompoundMotors:
    async with init_devices(mock=True):
        mock_compound = PolynomCompoundMotors(
            x_motor,
            {
                y_motor: np.array([1.0, 2.0], dtype=np.float64),
                z_motor: np.array([-1.0, 0.5], dtype=np.float64),
            },
            name="mock_compound",
        )
    return mock_compound


async def test_config_includes(mock_compound: PolynomCompoundMotors):
    await assert_configuration(
        mock_compound,
        {},
    )


async def test_read_includes(mock_compound: PolynomCompoundMotors):
    await assert_reading(
        mock_compound,
        {
            "x_motor": partial_reading(0.0),
            "y_motor": partial_reading(0.0),
            "z_motor": partial_reading(0.0),
        },
    )


async def test_move(
    mock_compound: PolynomCompoundMotors,
    run_engine: RunEngine,
):
    new_position = 10.0
    run_engine(bps.mv(mock_compound, new_position))
    for motor, coeff in mock_compound.motor_coeff_dict.items():
        expected_position = float(np.polynomial.polynomial.polyval(new_position, coeff))
        actual_position = await motor().user_readback.get_value()
        assert actual_position == expected_position


async def test_move_and_locate(
    mock_compound: PolynomCompoundMotors,
    run_engine: RunEngine,
):
    new_position = 1.23
    run_engine(bps.mv(mock_compound, new_position))
    located_position = await mock_compound.locate()
    assert located_position == {"setpoint": new_position, "readback": new_position}
