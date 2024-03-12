from ophyd_async.core import set_sim_value

from dodal.devices.robot import BartRobot


async def _get_bart_robot() -> BartRobot:
    device = BartRobot("robot", "-MO-ROBOT-01:")
    await device.connect(sim=True)
    return device


async def test_bart_robot_can_be_connected_in_sim_mode():
    device = await _get_bart_robot()
    await device.connect(sim=True)


async def test_when_barcode_updates_then_new_barcode_read():
    device = await _get_bart_robot()
    expected_barcode = "expected"
    set_sim_value(device.barcode.bare_signal, [expected_barcode, "other_barcode"])
    assert (await device.barcode.read())["robot-barcode"]["value"] == expected_barcode
