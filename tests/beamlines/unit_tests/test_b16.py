from unittest.mock import Mock

from dodal.devices.b16.detector import (
    ADTIFFWriter,
    AreaDetector,
    ConstantDeadTimeController,
    software_triggered_tiff_area_detector,
)


def test_constant_dead_time_controller_returns_constant():
    constant_deadtime = 2.4
    controller = ConstantDeadTimeController(driver=Mock(), deadtime=constant_deadtime)
    assert controller.get_deadtime(exposure=Mock()) == constant_deadtime


def test_software_triggered_tiff_area_detector():
    det = software_triggered_tiff_area_detector("PV_PREFIX:")

    # should return an AreaDetector...
    assert isinstance(det, AreaDetector)

    # ...with a ConstantDeadTimeController (deadtime defaulted to 0)
    assert isinstance(det._controller, ConstantDeadTimeController)
    assert det._controller.get_deadtime(Mock()) == 0.0

    # ...and a Tiff writer
    assert isinstance(det._writer, ADTIFFWriter)
