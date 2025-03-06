from unittest.mock import AsyncMock, MagicMock

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import set_mock_value

from dodal.devices.zebra.zebra import (
    ArmDemand,
    ArmingDevice,
    ArmSource,
    GateType,
    I03Axes,
    LogicGateConfiguration,
    LogicGateConfigurer,
    PositionCompare,
    RotationDirection,
    TrigSource,
    boolean_array_to_integer,
)


async def test_arming_device(RE: RunEngine):
    arming_device = ArmingDevice("", name="fake arming device")
    await arming_device.connect(mock=True)
    status = arming_device.set(ArmDemand.DISARM)
    await status
    assert status.success
    assert await arming_device.disarm_set.get_value() == 1


async def test_position_compare_sets_signals(RE: RunEngine):
    fake_pc = PositionCompare("", name="fake position compare")
    await fake_pc.connect(mock=True)

    async def mock_arm(demand):
        set_mock_value(fake_pc.arm.armed, demand)
        set_mock_value(fake_pc.arm.disarm_set, not demand)
        set_mock_value(fake_pc.arm.arm_set, demand)

    fake_pc.arm.arm_set.set = AsyncMock(side_effect=mock_arm)
    fake_pc.arm.disarm_set.set = AsyncMock(side_effect=mock_arm)

    await fake_pc.gate_source.set(TrigSource.EXTERNAL)
    await fake_pc.gate_trigger.set(I03Axes.OMEGA)
    await fake_pc.num_gates.set(10)

    assert await fake_pc.gate_source.get_value() == TrigSource.EXTERNAL
    assert await fake_pc.gate_trigger.get_value() == I03Axes.OMEGA
    assert await fake_pc.num_gates.get_value() == 10

    await fake_pc.arm_source.set(ArmSource.SOFT)
    status = fake_pc.arm.set(ArmDemand.ARM)
    await status

    assert await fake_pc.arm_source.get_value() == "Soft"
    assert await fake_pc.arm.arm_set.get_value() == 1
    assert await fake_pc.arm.disarm_set.get_value() == 0
    assert await fake_pc.is_armed()


@pytest.mark.parametrize(
    "boolean_array,expected_integer",
    [
        ([True, False, False], 1),
        ([True, False, True, False], 5),
        ([False, True, False, True], 10),
        ([False, False, False, False], 0),
        ([True, True, True], 7),
    ],
)
def test_boolean_array_to_integer(boolean_array, expected_integer):
    assert boolean_array_to_integer(boolean_array) == expected_integer


def test_logic_gate_configuration_23():
    config1 = LogicGateConfiguration(23)
    assert config1.sources == [23]
    assert config1.invert == [False]
    assert str(config1) == "INP1=23"


def test_logic_gate_configuration_43_and_14_inv():
    config = LogicGateConfiguration(43).add_input(14, True)
    assert config.sources == [43, 14]
    assert config.invert == [False, True]
    assert str(config) == "INP1=43, INP2=!14"


def test_logic_gate_configuration_62_and_34_inv_and_15_inv():
    config = LogicGateConfiguration(62).add_input(34, True).add_input(15, True)
    assert config.sources == [62, 34, 15]
    assert config.invert == [False, True, True]
    assert str(config) == "INP1=62, INP2=!34, INP3=!15"


async def run_configurer_test(
    gate_type: GateType, gate_num, config, expected_pv_values
):
    configurer = LogicGateConfigurer(prefix="", name="test fake logicconfigurer")
    await configurer.connect(mock=True)

    mock_gate_control = MagicMock()
    mock_pvs = [MagicMock() for i in range(6)]
    mock_gate_control.enable = mock_pvs[0]
    mock_gate_control.sources = {i: mock_pvs[i] for i in range(1, 5)}
    mock_gate_control.invert = mock_pvs[5]
    configurer.all_gates[gate_type][gate_num - 1] = mock_gate_control

    if gate_type == GateType.AND:
        configurer.apply_and_gate_config(gate_num, config)
    else:
        configurer.apply_or_gate_config(gate_num, config)

    for pv, value in zip(mock_pvs, expected_pv_values, strict=False):
        pv.set.assert_called_once_with(value)


async def test_apply_and_logic_gate_configuration_32_and_51_inv_and_1():
    config = LogicGateConfiguration(32).add_input(51, True).add_input(1)
    expected_pv_values = [7, 32, 51, 1, 0, 2]

    await run_configurer_test(GateType.AND, 1, config, expected_pv_values)


async def test_apply_or_logic_gate_configuration_19_and_36_inv_and_60_inv():
    config = LogicGateConfiguration(19).add_input(36, True).add_input(60, True)
    expected_pv_values = [7, 19, 36, 60, 0, 6]

    await run_configurer_test(GateType.OR, 2, config, expected_pv_values)


@pytest.mark.parametrize(
    "source",
    [-1, 67],
)
def test_logic_gate_configuration_with_invalid_source_then_error(source):
    with pytest.raises(AssertionError):
        LogicGateConfiguration(source)

    existing_config = LogicGateConfiguration(1)
    with pytest.raises(AssertionError):
        existing_config.add_input(source)


def test_logic_gate_configuration_with_too_many_sources_then_error():
    config = LogicGateConfiguration(0)
    for source in range(1, 4):
        config.add_input(source)

    with pytest.raises(AssertionError):
        config.add_input(5)


def test_direction_multiplier():
    assert RotationDirection.NEGATIVE.multiplier == -1
    assert RotationDirection.POSITIVE.multiplier == 1
