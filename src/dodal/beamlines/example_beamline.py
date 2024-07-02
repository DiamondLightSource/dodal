from functools import _Wrapped, wraps
from typing import Callable, Dict, Optional, TypeVar

from bluesky.run_engine import call_in_bluesky_event_loop
from ophyd_async.core import Device as OphydV2Device

from dodal.common.beamlines.beamline_utils import (
    ACTIVE_DEVICES,
    DEFAULT_CONNECTION_TIMEOUT,
)


class XYZDetector(OphydV2Device):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def hints(self):
        raise NotImplementedError


GenericDeviceTypeVar = TypeVar("GenericDeviceTypeVar", bound=OphydV2Device)

LAZY_DEVICES: Dict[str, OphydV2Device] = {}


class DeviceInitializationConfig:
    lazy: bool = False
    set_name: bool = True
    timeout: float = DEFAULT_CONNECTION_TIMEOUT  # todo possibly delete, as its already the default argument to connect
    use_mock: bool = (
        False  # todo possibly delete, as its already the default argument to connect
    )

    def __init__(self, **kwargs):
        self.lazy = kwargs.get("lazy", False)
        self.set_name = kwargs.get("set_name", True)
        self.timeout = kwargs.get("timeout", 0)
        self.use_mock = kwargs.get("use_mock", False)


class DeviceInitializationController:
    device: Optional[OphydV2Device] = None
    config: Optional[DeviceInitializationConfig] = None

    def __init__(self, config: DeviceInitializationConfig) -> None:
        self.config = config
        super().__init__()

    # TODO right now the cache is in a global variable ACTIVE_DEVICES, that should change
    def see_if_device_is_in_cache(self, name: str) -> Optional[GenericDeviceTypeVar]:
        d = ACTIVE_DEVICES.get(name)
        assert isinstance(d, OphydV2Device) or d is None
        return d

    def add_device_to_cache(self, device: GenericDeviceTypeVar) -> None:
        ACTIVE_DEVICES[device.name] = device

    # TODO right now the lazy devices are in a global variable LAZY_DEVICES, that should change
    def add_device_to_lazy_cache(self, device: OphydV2Device) -> None:
        print(f"Device {device.name} is lazy, not initializing now")
        LAZY_DEVICES[device.name] = device

    def initialize_device(
        self,
        factory: Callable[[], GenericDeviceTypeVar],
    ) -> GenericDeviceTypeVar:
        assert self.config is not None

        device: GenericDeviceTypeVar = (
            # todo if we do not pass the name to the factory, we can not check if the device is in the cache.
            # there are many devices from the same factory
            self.see_if_device_is_in_cache(factory.__name__) or factory()
        )

        if self.config.set_name:
            # todo what if we have multiple devices from the same factory?
            device.set_name(factory.__name__)

        if self.config.lazy:
            self.add_device_to_lazy_cache(device)
        else:
            self.add_device_to_cache(device)
            call_in_bluesky_event_loop(
                device.connect(timeout=self.config.timeout, mock=self.config.use_mock)
            )
        return device


def device_instance_behavior(
    **config_kwargs,
) -> Callable[[Callable[[], GenericDeviceTypeVar]], _Wrapped]:
    config = DeviceInitializationConfig(**config_kwargs)

    def decorator(factory):
        controller = DeviceInitializationController(config=config)

        @wraps(factory)
        def wrapper(*args, **kwargs) -> GenericDeviceTypeVar:
            return controller.initialize_device(factory, *args, **kwargs)

        return wrapper

    return decorator


beamline_prefix = "example:"


@device_instance_behavior(lazy=True, use_mock=True, timeout=10)
def detector_xyz():
    """Create an XYZ detector with specific settings."""
    return XYZDetector(name="det1", prefix=f"{beamline_prefix}xyz:")
