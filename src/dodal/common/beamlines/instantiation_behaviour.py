from collections.abc import Callable
from dataclasses import dataclass

from bluesky.run_engine import call_in_bluesky_event_loop
from ophyd_async.core import DEFAULT_TIMEOUT
from ophyd_async.core import Device as OphydV2Device

from dodal.common.beamlines.beamline_utils import (
    ACTIVE_DEVICES,
)
from dodal.utils import AnyDevice


class XYZDetector(OphydV2Device):
    def __init__(self, prefix: str, *args, **kwargs):
        self.prefix = prefix
        super().__init__(*args, **kwargs)

    @property
    def hints(self):
        raise NotImplementedError


@dataclass
class DeviceInitializationConfig:
    """
    eager ones all connect at the beginning in blueapi startup. if they fail to connect we get an error
    endpoint for what devices are failing
    only matters in connect failure reporting behavior
    lazy and eager are not about when connect but whether should be connected
    """

    eager: bool = True
    set_name: bool = True
    default_timeout_for_connect: float = DEFAULT_TIMEOUT
    default_use_mock_at_connection: bool = False


class DeviceInitializationController:
    """
    This class is responsible for the instantiation of a device.
    The device is then cached here locally, and also in the global variable ACTIVE_DEVICES.
    """

    device: AnyDevice | None = None
    factory: Callable[[], AnyDevice]

    def __init__(
        self, config: DeviceInitializationConfig, factory: Callable[[], AnyDevice]
    ) -> None:
        self.factory = factory
        self.config = config
        CONTROLLERS[self.factory.__name__] = self
        self.device = None

    # TODO right now the cache is in a global variable ACTIVE_DEVICES, that should change
    def see_if_device_is_in_cache(self) -> AnyDevice | None:
        return self.device

    def __call__(
        self,
        connect=False,
        mock: bool | None = None,
        timeout: float | None = None,
        name: str | None = None,
    ) -> AnyDevice:
        device: AnyDevice = (
            # todo if we do not pass the name to the factory, we can not check if the device is in the cache.
            # there are many devices from the same factory
            self.see_if_device_is_in_cache() or self.factory()
        )
        assert device is not None
        if self.config.set_name:
            device.set_name(self.factory.__name__)
        self.add_device_to_cache(device)

        if connect:
            call_in_bluesky_event_loop(
                device.connect(
                    timeout=self.config.default_timeout_for_connect
                    if timeout is None
                    else timeout,
                    mock=self.config.default_use_mock_at_connection
                    if mock is None
                    else mock,
                )
            )
            assert self.device is not None
            CONTROLLERS[self.device.name] = self

        if self.device is not None:
            CONTROLLERS[self.device.name] = self
        return device

    def add_device_to_cache(self, device: AnyDevice) -> None:
        self.device = device
        ACTIVE_DEVICES[device.name] = device


CONTROLLERS: dict[str, DeviceInitializationController] = {}


def instantiation_behaviour(
    *,
    eager: bool = True,
    set_name: bool = True,
    default_timeout_for_connect: float = DEFAULT_TIMEOUT,
    default_use_mock_at_connection: bool = False,
) -> Callable[[Callable[[], AnyDevice]], DeviceInitializationController]:
    config = DeviceInitializationConfig(
        eager, set_name, default_timeout_for_connect, default_use_mock_at_connection
    )

    def decorator(factory: Callable[[], AnyDevice]) -> DeviceInitializationController:
        controller = DeviceInitializationController(config, factory)
        return controller

    return decorator


beamline_prefix = "example:"


@instantiation_behaviour(
    default_use_mock_at_connection=True, default_timeout_for_connect=10
)
def new_detector_xyz():
    """Create an XYZ detector with specific settings."""
    return XYZDetector(name="det1", prefix=f"{beamline_prefix}xyz:")


@instantiation_behaviour(
    eager=True, default_use_mock_at_connection=True, default_timeout_for_connect=10
)
def detector_xyz_variant():
    """Create an XYZ detector with specific settings."""
    return XYZDetector(name="det2-variant", prefix=f"{beamline_prefix}xyz:")
