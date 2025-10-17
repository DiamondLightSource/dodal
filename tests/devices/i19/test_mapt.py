import pytest
from ophyd_async.core import DeviceVector, SubsetEnum, init_devices
from ophyd_async.testing import assert_reading, partial_reading, set_mock_value

from dodal.devices.i19.mapt_configuration import (
    MAPTConfigurationControl,
    MAPTConfigurationTable,
)


class ConfigEnumTest(SubsetEnum):
    TEN = "10um"
    TWENTY = "20um"


@pytest.fixture
async def mapt_table() -> MAPTConfigurationTable:
    async with init_devices(mock=True):
        mapt = MAPTConfigurationTable("", "FakeMotor", [10, 20], "test_mapt")
    set_mock_value(mapt.in_positions[10], 30)
    set_mock_value(mapt.in_positions[20], 18)
    return mapt


@pytest.fixture
async def mapt_control() -> MAPTConfigurationControl:
    async with init_devices(mock=True):
        mapt_c = MAPTConfigurationControl("", ConfigEnumTest, "test_control")
    set_mock_value(mapt_c.select_config, ConfigEnumTest.TEN)
    return mapt_c


def test_mapt_table_created_without_errors():
    mapt = MAPTConfigurationTable("", "FakeMotor", [5], "test_mapt")
    assert isinstance(mapt, MAPTConfigurationTable)
    assert isinstance(mapt.in_positions, DeviceVector)


async def test_mapt_table_can_be_read(mapt_table: MAPTConfigurationTable):
    await assert_reading(
        mapt_table,
        {
            "test_mapt-in_positions-10": partial_reading(30),
            "test_mapt-in_positions-20": partial_reading(18),
        },
    )


def test_mapt_control_created_without_errors():
    control = MAPTConfigurationControl("", ConfigEnumTest, "test_control")
    assert isinstance(control, MAPTConfigurationControl)


async def test_mapt_control_signal_can_be_read(mapt_control: MAPTConfigurationControl):
    await assert_reading(
        mapt_control, {"test_control-select_config": partial_reading("10um")}
    )


async def test_select_new_config_value(mapt_control: MAPTConfigurationControl):
    await mapt_control.select_config.set(ConfigEnumTest.TWENTY)

    assert await mapt_control.select_config.get_value() == "20um"
