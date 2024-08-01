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
    instantiation_behaviour,
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

        def factory():
            return self.device_mock

        controller = DeviceInitializationController(self.config, factory)

        controller.add_device_to_cache(self.device_mock)
        cached_device = controller.see_if_device_is_in_cache(self.device_mock.name)

        self.assertEqual(cached_device, self.device_mock)

    def test_device_creation_and_connection(self):
        def factory():
            return self.device_mock

        controller = DeviceInitializationController(self.config, factory)

        with patch(
            "dodal.common.beamlines.instantiation_behaviour.call_in_bluesky_event_loop"
        ) as mock_event_loop:
            with patch.object(self.device_mock, "connect") as mock_connect:
                mock_connect.return_value = MagicMock()
                _device = controller(connect=True)

                mock_connect.assert_called_once_with(
                    timeout=DEFAULT_TIMEOUT, mock=False
                )
                mock_event_loop.assert_called_once_with(mock_connect())


class TestInstantiationBehaviour(unittest.TestCase):
    def test_decorator_creates_controller(self):
        def factory():
            return MagicMock(spec=XYZDetector)

        decorator = instantiation_behaviour()
        controller = decorator(factory)

        self.assertIsInstance(controller, DeviceInitializationController)
        self.assertIn(factory.__name__, CONTROLLERS)


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
