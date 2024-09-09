from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, ParamSpec, TypeVar

from bluesky.run_engine import call_in_bluesky_event_loop
from ophyd_async.core import DEFAULT_TIMEOUT, Device

from dodal.common.beamlines.beamline_utils import ACTIVE_DEVICES

P = ParamSpec("P")
T = TypeVar("T", bound=Device)
_skip = bool | Callable[[], bool]


@dataclass
class DeviceInitializationConfig:
    """
    eager_connect: connect or raise Exception at startup
    use_factory_name: use factory name as name of device
    timeout: timeout for connecting to the device
    mock: use Signals with mock backends for device
    skip: mark the factory to be (conditionally) skipped
    """

    eager_connect: bool
    use_factory_name: bool
    timeout: float
    mock: bool
    skip: _skip


class DeviceInitializationController(Generic[P, T]):
    def __init__(self, config: DeviceInitializationConfig, factory: Callable[P, T]):
        self._factory: Callable[P, T] = factory
        self._config: DeviceInitializationConfig = config
        self._cached_device: T | None = None

    @property
    def skip(self) -> bool:
        return self._config.skip() if callable(self._config.skip) else self._config.skip

    @property
    def device(self) -> T | None:
        return self._cached_device

    def __call__(
        self,
        connect: bool | None = None,
        name: str | None = None,
        timeout: float | None = None,
        mock: bool | None = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        # that is for the second and later times the device is called
        if self.device is not None:
            return self.device

        # unpack the arguments, fill in the defaults
        connect = self._config.eager_connect if connect is None else connect
        name = name or (
            self._factory.__name__ if self._config.use_factory_name else None
        )
        mock = self._config.mock if mock is None else mock
        timeout = timeout or self._config.timeout

        # the instantiation of the device
        device = self._factory(*args, **kwargs)
        if name:
            device.set_name(name)

        # connect the device if needed
        if connect:
            call_in_bluesky_event_loop(
                device.connect(
                    timeout=timeout,
                    mock=mock,
                )
            )

        self._cache_device(device)
        return device

    def _cache_device(self, device: T):
        if device.name:
            ACTIVE_DEVICES[device.name] = device
        self._cached_device = device


def device_factory(
    *,
    eager: bool = True,
    use_factory_name: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
    mock: bool = False,
    skip: _skip = False,
) -> Callable[[Callable[P, T]], DeviceInitializationController[P, T]]:
    config = DeviceInitializationConfig(
        eager,
        use_factory_name,
        timeout,
        mock,
        skip,
    )

    def decorator(factory: Callable[P, T]) -> DeviceInitializationController[P, T]:
        return DeviceInitializationController(
            config,
            factory,
        )

    return decorator
