from unittest.mock import Mock

import pytest

from dodal.devices.controllers import (
    ConstantDeadTimeController,
)


@pytest.mark.parametrize("exposure", [0.001, 0.01, 0.1, 1, 10, 100])
def test_constant_dead_time_controller_returns_constant(exposure: float):
    deadtime = 0.7
    controller = ConstantDeadTimeController(driver=Mock(), deadtime=deadtime)
    # Check that the exposure value given is ignored and used the configured constant
    # value instead.
    assert controller.get_deadtime(exposure) == deadtime
