import numpy as np
import pytest
from ophyd_async.core import init_devices
from ophyd_async.epics.motor import Motor
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.i05 import PolynomCompoundMotors


@pytest.fixture
async def x_motor() -> Motor:
    async with init_devices(mock=True):
        x_motor = Motor("")
    return x_motor


@pytest.fixture
async def y_motor() -> Motor:
    async with init_devices(mock=True):
        y_motor = Motor("")
    return y_motor


@pytest.fixture
async def z_motor() -> Motor:
    async with init_devices(mock=True):
        z_motor = Motor("")
    return z_motor


@pytest.fixture
async def mock_compound(
    x_motor: Motor,
    y_motor: Motor,
    z_motor: Motor,
) -> PolynomCompoundMotors:
    async with init_devices(mock=True):
        mock_compound = PolynomCompoundMotors(
            master_motor=x_motor,
            slaves_dict={
                y_motor: np.array([0.0, 1.0], dtype=np.float64),
                z_motor: np.array([0.0, 1.0], dtype=np.float64),
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
