import unittest
from unittest.mock import MagicMock

from ophyd_async.core import DEFAULT_TIMEOUT
from ophyd_async.core import Device as OphydV2Device

from dodal.common.beamlines.beamline_utils import ACTIVE_DEVICES
from dodal.common.beamlines.device_factory import (
    DeviceInitializationConfig,
    device_factory,
)


class XYZDetector(OphydV2Device):
    def __init__(self, prefix: str, *args, **kwargs):
        self.prefix = prefix
        super().__init__(*args, **kwargs)

    @property
    def hints(self):
        raise NotImplementedError


beamline_prefix = "example:"


def test_decorator_directly():
    ACTIVE_DEVICES.clear()
    beamline_prefix = "example:"

    @device_factory(eager=False)
    def detector_xyz_variant():
        """Create an XYZ detector with specific settings."""
        return XYZDetector(name="det2-variant", prefix=f"{beamline_prefix}xyz:")

    device = detector_xyz_variant()
    assert device is not None
    assert "detector_xyz_variant" in ACTIVE_DEVICES.keys()


def test_decorator_directly_with_no_name_override():
    ACTIVE_DEVICES.clear()
    beamline_prefix = "example:"

    @device_factory(mock=True)
    def detector_xyz_variant():
        """Create an XYZ detector with specific settings."""
        return XYZDetector(name="foo", prefix=f"{beamline_prefix}xyz:")

    device = detector_xyz_variant()
    assert device is not None
    assert "foo" in ACTIVE_DEVICES.keys()


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
        config = device_factory()
        self.assertTrue(config.eager)
        self.assertTrue(config.set_name)
        self.assertEqual(config.default_timeout_for_connect, DEFAULT_TIMEOUT)
        self.assertFalse(config.default_use_mock_at_connection)

    def test_custom_values(self):
        config = DeviceInitializationConfig(
            eager_connect=False,
            use_factory_name=False,
            timeout=5.0,
            mock=True,
            skip=True,
        )
        assert not config.eager_connect
        assert not config.use_factory_name
        assert config.timeout == 5.0
        assert config.mock
        assert config.skip


class TestDeviceInitializationController(unittest.TestCase):
    def setUp(self):
        self.config = DeviceInitializationConfig(
            eager_connect=False,
            use_factory_name=False,
            timeout=5.0,
            mock=True,
            skip=True,
        )
        self.device_mock = MagicMock(spec=XYZDetector)
        self.device_mock.name = "mock_device"

    def test_device_caching(self):
        @device_factory()
        def my_device():
            return self.device_mock

        ACTIVE_DEVICES.clear()

        d = my_device()

        cached_device = d.device()
        assert cached_device is not None

        assert "my_device" in ACTIVE_DEVICES
        assert ACTIVE_DEVICES["my_device"] is self.device_mock
