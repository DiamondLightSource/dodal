from unittest.mock import Mock

from dodal.devices.i18.sim_detector import SimDetector


def test_simdetector_read():
    """
    Test SimDetector.read() returns a pattern generator value in the correct structure.
    """
    motor_mock = Mock()
    pattern_generator_mock = Mock()
    pattern_generator_mock.return_value = {"value": pattern_generator_mock}

    detector = SimDetector(name="detector1", motor=motor_mock, motor_field="position")
    detector.pattern_generator = (
        pattern_generator_mock  # Replace actual generator with mock for testing
    )

    result = detector.read()

    # Check the structure and value
    assert result == {"detector1": {"value": pattern_generator_mock}}


def test_simdetector_describe():
    """
    Test SimDetector.describe() returns correct metadata.
    """
    motor_mock = Mock()
    detector = SimDetector(name="detector1", motor=motor_mock, motor_field="position")

    result = detector.describe()

    # Check the structure and value
    assert result == {"detector1": {"source": "synthetic", "dtype": "number"}}
