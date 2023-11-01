import pytest
from ophyd_async.core import set_sim_value

from dodal.devices.smargon import LimitsChecker, Smargon, StubOffsets, StubPosition


async def _get_smargon() -> Smargon:
    device = Smargon("-MO-SGON-01:", "smargon")
    await device.connect(sim=True)
    return device


async def _get_stub_offsets_device() -> StubOffsets:
    return (await _get_smargon()).stub_offsets


async def _get_limit_check_device() -> LimitsChecker:
    return (await _get_smargon()).limit_checker


@pytest.mark.asyncio
async def test_smargon_can_be_connected_in_sim_mode():
    device = await _get_stub_offsets_device()
    await device.connect(sim=True)


@pytest.mark.asyncio
async def test_given_stub_offset_center_enabled_when_move_to_center_then_moves():
    device = await _get_stub_offsets_device()

    set_sim_value(device.center_at_current_position.disp, 0)

    await device.set(StubPosition.CURRENT_AS_CENTER)

    assert await device.center_at_current_position.proc.get_value() == 1


@pytest.mark.asyncio
async def test_given_stub_offset_center_disabled_when_move_to_center_then_not_moved_until_enabled():
    device = await _get_stub_offsets_device()

    set_sim_value(device.center_at_current_position.disp, 1)

    status = device.set(StubPosition.CURRENT_AS_CENTER)

    assert await device.center_at_current_position.proc.get_value() == 0

    set_sim_value(device.center_at_current_position.disp, 0)

    await status

    assert await device.center_at_current_position.proc.get_value() == 1


@pytest.mark.asyncio
async def test_given_stub_offset_to_robot_load_enabled_when_move_to_robot_load_then_moves():
    device = await _get_stub_offsets_device()

    set_sim_value(device.to_robot_load.disp, 0)

    await device.set(StubPosition.RESEET_TO_ROBOT_LOAD)

    assert await device.to_robot_load.proc.get_value() == 1


@pytest.mark.asyncio
async def test_given_stub_offset_to_robot_load_disabled_when_move_to_robot_load_then_not_moved_until_enabled():
    device = await _get_stub_offsets_device()

    set_sim_value(device.to_robot_load.disp, 1)

    status = device.set(StubPosition.RESEET_TO_ROBOT_LOAD)

    assert await device.to_robot_load.proc.get_value() == 0

    set_sim_value(device.to_robot_load.disp, 0)

    await status

    assert await device.to_robot_load.proc.get_value() == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "position, expected_within",
    [
        ([0.1, 0.1, 0.1], True),
        ([1.8, 0.1, 0.1], False),
        ([0.8, -0.8, 0.1], False),
        ([0.6, 0.1, 20.3], False),
        ([0.6, 78.0, 20.3], False),
    ],
)
async def test_given_x_y_z_limits_set_when_in_limits_checker_then_expected(
    position, expected_within
):
    xyz_limit_checker = await _get_limit_check_device()

    for axis in xyz_limit_checker.axes:
        set_sim_value(axis.low_limit_travel, 0)
        set_sim_value(axis.high_limit_travel, 1)

    await xyz_limit_checker.set(position)
    assert xyz_limit_checker.within_limits == expected_within
