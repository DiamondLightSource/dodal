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


T = TypeVar("T", bound=OphydV2Device)

LAZY_DEVICES: Dict[str, OphydV2Device] = {}


@dataclass
class DeviceInitalizationConfig:
    name: str
    prefix: str
    lazy: bool = False
    fake: bool = False
    timeout: float = DEFAULT_CONNECTION_TIMEOUT
    bl_prefix: bool = True


class DeviceInitalizationController:
    device: Optional[OphydV2Device] = None
    config: Optional[DeviceInitalizationConfig] = None

    def __init__(self, config: DeviceInitalizationConfig) -> None:
        self.config = config
        super().__init__()

    # TODO right now the cache is in a global variable ACTIVE_DEVICES, that should change
    def see_if_device_is_in_cache(self, name: str) -> Optional[OphydV2Device]:
        d = ACTIVE_DEVICES.get(name)
        assert d is OphydV2Device
        # todo temporarily throw an error if the device is from v1
        return d

    # todo splitting the logic for initalizing the device and the logic for caching the device
    # potentially more features too
    def initalize_device(
        self,
        factory: Callable[[], T],
        post_create: Optional[Callable[[T], None]] = None,
    ) -> T:
        assert self.config is not None

        # todo add fake and cache logic
        cached_device = self.see_if_device_is_in_cache(self.config.name)
        # todo should we run the post-create again if we recover from cache?
        if self.config.fake:
            # todo not sure what is the ophyd-2 faking logic
            pass
        device = factory()
        if self.config.lazy:
            print(f"Device {factory.__name__} is lazy, not initalizing now")
            LAZY_DEVICES[self.config.name] = device
        else:
            call_in_bluesky_event_loop(device.connect(timeout=self.config.timeout))
        if self.config.fake:
            print("Running in fake mode")
        if post_create:
            post_create(device)
        return device


def instance_behavior(
    config: DeviceInitalizationConfig,
    post_create: Optional[Callable[[T], None]] = None,
) -> Callable[[Callable[[], T]], _Wrapped]:
    def decorator(device_specific_subclass):
        controller = DeviceInitalizationController(config=config)

        @wraps(device_specific_subclass)
        def wrapper(*args, **kwargs) -> OphydV2Device:
            return controller.initalize_device(device_specific_subclass, post_create)

        return wrapper

    return decorator


@instance_behavior(
    config=DeviceInitalizationConfig(
        name="det1", prefix="xyz:", lazy=True, fake=True, timeout=10
    ),
    post_create=None,
)
def detector_xyz() -> XYZDetector:
    return XYZDetector()
