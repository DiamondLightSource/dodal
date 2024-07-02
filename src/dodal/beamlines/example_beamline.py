from dataclasses import dataclass
from functools import _Wrapped, wraps
from typing import Callable, Dict, Optional, TypeVar

from bluesky.run_engine import call_in_bluesky_event_loop
from ophyd_async.core import Device as OphydV2Device

from dodal.common.beamlines.beamline_utils import (
    ACTIVE_DEVICES,
    DEFAULT_CONNECTION_TIMEOUT,
)


class XYZDetector:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def hints(self):
        raise NotImplementedError


GenericDeviceTypeVar = TypeVar("GenericDeviceTypeVar", bound=OphydV2Device)

LAZY_DEVICES: Dict[str, OphydV2Device] = {}


@dataclass
class DeviceInitalizationConfig:
    name: str
    prefix: str
    lazy: bool = False
    use_mock: bool = False
    timeout: float = DEFAULT_CONNECTION_TIMEOUT
    bl_prefix: bool = True
    set_name: bool = True


@dataclass
class DeviceArguments:
    # todo how to sort this out?
    name: str
    prefix: str


class DeviceInitalizationController:
    device: Optional[OphydV2Device] = None
    config: Optional[DeviceInitalizationConfig] = None

    def __init__(self, config: DeviceInitalizationConfig) -> None:
        self.config = config
        super().__init__()

    # TODO right now the cache is in a global variable ACTIVE_DEVICES, that should change
    def see_if_device_is_in_cache(self, name: str) -> Optional[GenericDeviceTypeVar]:
        d = ACTIVE_DEVICES.get(name)
        assert d is OphydV2Device
        return d

    def add_device_to_cache(self, device: GenericDeviceTypeVar) -> None:
        ACTIVE_DEVICES[device.name] = device

    # TODO right now the lazy devices are in a global variable LAZY_DEVICES, that should change
    def add_device_to_lazy_cache(self, device: OphydV2Device) -> None:
        print(f"Device {device.name} is lazy, not initalizing now")
        LAZY_DEVICES[device.name] = device

    def initalize_device(
        self,
        factory: Callable[[], GenericDeviceTypeVar],
    ) -> GenericDeviceTypeVar:
        assert self.config is not None

        device: GenericDeviceTypeVar = (
            self.see_if_device_is_in_cache(self.config.name) or factory()
        )

        if self.config.set_name:
            device.set_name(factory.__name__)

        if self.config.lazy:
            self.add_device_to_lazy_cache(device)
        else:
            self.add_device_to_cache(device)
            call_in_bluesky_event_loop(
                device.connect(timeout=self.config.timeout, mock=self.config.use_mock)
            )
        return device


def instance_behavior(
    config: DeviceInitalizationConfig,
) -> Callable[[Callable[[], GenericDeviceTypeVar]], _Wrapped]:
    def decorator(device_specific_subclass):
        controller = DeviceInitalizationController(config=config)

        @wraps(device_specific_subclass)
        def wrapper(*args, **kwargs) -> GenericDeviceTypeVar:
            return controller.initalize_device(device_specific_subclass)

        return wrapper

    return decorator


@instance_behavior(
    config=DeviceInitalizationConfig(lazy=True, use_mock=True, timeout=10),
)
def detector_xyz() -> XYZDetector:
    return XYZDetector(name="det1", prefix="xyz:")
