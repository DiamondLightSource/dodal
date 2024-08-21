import unittest
from unittest.mock import MagicMock, patch

from ophyd_async.core import DEFAULT_TIMEOUT

from dodal.common.beamlines.beamline_utils import ACTIVE_DEVICES
from dodal.common.beamlines.instantiation_behaviour import (
    CONTROLLERS,
    DeviceInitializationConfig,
    DeviceInitializationController,
    XYZDetector,
    detector_xyz_variant,
    new_detector_xyz,
)


class TestXYZDetector(unittest.TestCase):
    def test_initialization(self):
        detector = XYZDetector(prefix="test:")
        self.assertEqual(detector.prefix, "test:")

    def test_hints_property(self):
        detector = XYZDetector(prefix="test:")
        with self.assertRaises(NotImplementedError):
            _ = detector.hints


class TestDeviceInitializationConfig(unittest.TestCase):
    def test_default_values(self):
        config = DeviceInitializationConfig()
        self.assertTrue(config.eager)
        self.assertTrue(config.set_name)
        self.assertEqual(config.default_timeout_for_connect, DEFAULT_TIMEOUT)
        self.assertFalse(config.default_use_mock_at_connection)

    def test_custom_values(self):
        config = DeviceInitializationConfig(
            eager=False,
            set_name=False,
            default_timeout_for_connect=5.0,
            default_use_mock_at_connection=True,
        )
        self.assertFalse(config.eager)
        self.assertFalse(config.set_name)
        self.assertEqual(config.default_timeout_for_connect, 5.0)
        self.assertTrue(config.default_use_mock_at_connection)


class TestDeviceInitializationController(unittest.TestCase):
    def setUp(self):
        self.config = DeviceInitializationConfig()
        self.device_mock = MagicMock(spec=XYZDetector)
        self.device_mock.name = "mock_device"

    def test_controller_registration(self):
        def factory():
            return self.device_mock

        controller = DeviceInitializationController(self.config, factory)
        self.assertIn(factory.__name__, CONTROLLERS)
        self.assertEqual(CONTROLLERS[factory.__name__], controller)

    def test_device_caching(self):
        ACTIVE_DEVICES.clear()

        def my_device():
            return self.device_mock

        controller = DeviceInitializationController(self.config, my_device)

        controller.add_device_to_cache(self.device_mock)
        cached_device = controller.see_if_device_is_in_cache("my_device")
        assert cached_device is not None

        self.assertEqual(cached_device, self.device_mock)

    def test_device_caching_with_name_override(self):
        ACTIVE_DEVICES.clear()

        def my_device():
            self.device_mock.name = "foo"
            return self.device_mock

        self.config.set_name = False
        controller = DeviceInitializationController(self.config, my_device)

        controller.add_device_to_cache(self.device_mock)
        cached_device = controller.see_if_device_is_in_cache("my_device")

        assert cached_device is not None
        self.assertEqual(cached_device, self.device_mock)
        assert cached_device.name == "foo"


class TestSpecificDeviceFunctions(unittest.TestCase):
    def test_new_detector_xyz(self):
        with patch(
            "dodal.common.beamlines.instantiation_behaviour.XYZDetector"
        ) as MockXYZDetector:
            new_detector_xyz()
            MockXYZDetector.assert_called_once_with(name="det1", prefix="example:xyz:")

    def test_detector_xyz_variant(self):
        with patch(
            "dodal.common.beamlines.instantiation_behaviour.XYZDetector"
        ) as MockXYZDetector:
            detector_xyz_variant()
            MockXYZDetector.assert_called_once_with(
                name="det2-variant", prefix="example:xyz:"
            )


if __name__ == "__main__":
    unittest.main()