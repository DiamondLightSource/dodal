from unittest.mock import Mock

from dodal.devices.b16.detector import ConstantDeadTimeController


def test_constant_dead_time_controller_returns_constant():
    constant_deadtime = 2.4
    controller = ConstantDeadTimeController(driver=Mock(), deadtime=constant_deadtime)
    assert controller.get_deadtime(exposure=Mock()) == constant_deadtime
