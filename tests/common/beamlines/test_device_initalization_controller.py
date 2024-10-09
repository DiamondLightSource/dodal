from unittest.mock import Mock, create_autospec

import pytest

from dodal.aliases import AnyDevice
from dodal.common.beamlines.device_factory import (
    DeviceInitializationConfig,
    DeviceInitializationController,
)


@pytest.fixture
def device_factory():
    """Fixture for creating a mock device factory."""
    return create_autospec(callable=True, spec=device_factory)


@pytest.fixture
def device_config():
    """Fixture for creating a mock device initialization config."""
    config = Mock(spec=DeviceInitializationConfig)
    config.eager_connect = False
    config.use_factory_name = False
    config.timeout = 5.0
    config.mock = False
    return config


@pytest.fixture
def controller(device_factory, device_config):
    """Fixture for creating a DeviceInitializationController instance."""
    return DeviceInitializationController(config=device_config, factory=device_factory)


def test_skip_property_with_boolean(controller):
    # Set the skip property to a boolean value
    controller._config.skip = False
    assert controller.skip is False

    controller._config.skip = True
    assert controller.skip is True


def test_skip_property_with_callable(controller):
    # Set the skip property to a callable that returns a boolean value
    controller._config.skip = Mock(return_value=True)
    assert controller.skip is True

    controller._config.skip = Mock(return_value=False)
    assert controller.skip is False


def test_repr_method(controller):
    # Mock a device object
    mock_device = Mock(spec=AnyDevice)
    mock_device.name = "TestDevice"

    # Set up the factory and config mock details
    controller._factory = Mock(return_value=mock_device)
    controller._config.eager_connect = True
    controller._config.use_factory_name = True
    controller._config.timeout = 10.0
    controller._config.mock = True
    controller._config.skip = Mock(return_value=False)

    # Call the controller to cache the device
    controller._cache_device(mock_device)

    representation = repr(controller)
    assert "Device initalization controller with:" in representation
    assert "use_factory_name: True" in representation
    assert "timeout: 10.0" in representation


def test_device_property_no_cached_device(controller):
    assert controller.device is None  # When no device has been cached


def test_device_property_with_cached_device(controller):
    # Mock a device object and cache it
    mock_device = Mock(spec=AnyDevice)
    mock_device.name = "CachedDevice"
    controller._cache_device(mock_device)

    assert controller.device is mock_device  # When a device has been cached
