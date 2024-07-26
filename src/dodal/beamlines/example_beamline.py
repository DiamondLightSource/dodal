from collections.abc import Callable

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

    def __init__(self, **kwargs):
        self.eager = kwargs.get("eager", False)
        self.set_name = kwargs.get("set_name", True)
        self.default_timeout_for_connect = kwargs.get("timeout", 0)
        self.default_use_mock_at_connection = kwargs.get(
            "use_mock_at_connection", False
        )


class DeviceInitializationController:
    device: AnyDevice | None = None
    config: DeviceInitializationConfig | None = None

    def __init__(self, config: DeviceInitializationConfig) -> None:
        self.config = config
        super().__init__()

    # TODO right now the cache is in a global variable ACTIVE_DEVICES, that should change
    def see_if_device_is_in_cache(self, name: str) -> AnyDevice | None:
        d = ACTIVE_DEVICES.get(name)
        assert isinstance(d, AnyDevice) or d is None
        return d

    def add_device_to_cache(self, device: AnyDevice) -> None:
        ACTIVE_DEVICES[device.name] = device

    def __call__(
        self,
        factory: Callable[[], AnyDevice],
    ) -> AnyDevice:
        assert self.config is not None

        device: AnyDevice = (
            # todo if we do not pass the name to the factory, we can not check if the device is in the cache.
            # there are many devices from the same factory
            self.see_if_device_is_in_cache(factory.__name__) or factory()
        )

        if self.config.set_name:
            device.set_name(factory.__name__)

        if self.config.eager:
            self.add_device_to_cache(device)
            call_in_bluesky_event_loop(
                device.connect(
                    timeout=self.config.default_timeout_for_connect,
                    mock=self.config.default_use_mock_at_connection,
                )
            )

        return device


def instantiation_behaviour(
    eager: bool = True
    set_name: bool = True
    default_timeout_for_connect: float = DEFAULT_TIMEOUT
    default_use_mock_at_connection: bool = False
) -> Callable[[Callable[[], AnyDevice]], DeviceInitializationController]:
    config = DeviceInitializationConfig(eager, set_name, default_timeout_for_connect, default_use_mock_at_connection)

    def decorator(factory: Callable[[], AnyDevice]) -> DeviceInitializationController:
        controller = DeviceInitializationController(config, factory)
        return controller

    return decorator


beamline_prefix = "example:"


@instantiation_behaviour(use_mock=True, timeout=10)
def detector_xyz():
    """Create an XYZ detector with specific settings."""
    return XYZDetector(name="det1", prefix=f"{beamline_prefix}xyz:")


@instantiation_behaviour(eager=True, use_mock=True, timeout=10)
def detector_xyz_variant():
    """Create an XYZ detector with specific settings."""
    return XYZDetector(name="det2-variant", prefix=f"{beamline_prefix}xyz:")


cached_controllers: dict[str, DeviceInitializationController] = {
    "det1": detector_xyz,
    "det2": detector_xyz_variant,
}
