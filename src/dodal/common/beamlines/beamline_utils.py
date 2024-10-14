import inspect
from collections.abc import Callable
from functools import update_wrapper
from typing import Annotated, Final, Generic, TypeVar, cast

from bluesky.run_engine import call_in_bluesky_event_loop
from ophyd import Device as OphydV1Device
from ophyd.sim import make_fake_device
from ophyd_async.core import DEFAULT_TIMEOUT
from ophyd_async.core import Device as OphydV2Device
from ophyd_async.core import wait_for_connection as v2_device_wait_for_connection

from dodal.common.types import UpdatingPathProvider
from dodal.utils import AnyDevice, BeamlinePrefix, skip_device

DEFAULT_CONNECTION_TIMEOUT: Final[float] = 5.0

ACTIVE_DEVICES: dict[str, AnyDevice] = {}
BL = ""
PATH_PROVIDER: UpdatingPathProvider | None = None


def set_beamline(beamline: str):
    global BL
    BL = beamline


def clear_devices():
    global ACTIVE_DEVICES
    for d in list(ACTIVE_DEVICES):
        del ACTIVE_DEVICES[d]


def clear_device(name: str):
    global ACTIVE_DEVICES
    del ACTIVE_DEVICES[name]


def list_active_devices() -> list[str]:
    global ACTIVE_DEVICES
    return list(ACTIVE_DEVICES.keys())


def active_device_is_same_type(
    active_device: AnyDevice, device: Callable[..., AnyDevice]
) -> bool:
    return inspect.isclass(device) and isinstance(active_device, device)


def wait_for_connection(
    device: AnyDevice,
    timeout: float = DEFAULT_CONNECTION_TIMEOUT,
    mock: bool = False,
) -> None:
    if isinstance(device, OphydV1Device):
        device.wait_for_connection(timeout=timeout)
    elif isinstance(device, OphydV2Device):
        call_in_bluesky_event_loop(
            v2_device_wait_for_connection(
                coros=device.connect(mock=mock, timeout=timeout)
            ),
        )
    else:
        raise TypeError(
            f"Invalid type {device.__class__.__name__} in _wait_for_connection"
        )


T = TypeVar("T", bound=AnyDevice)


@skip_device()
def device_instantiation(
    device_factory: Callable[..., T],
    name: str,
    prefix: str,
    wait: bool,
    fake: bool,
    post_create: Callable[[T], None] | None = None,
    bl_prefix: bool = True,
    **kwargs,
) -> T:
    """Method to allow generic creation of singleton devices. Meant to be used to easily
    define lists of devices in beamline files. Additional keyword arguments are passed
    directly to the device constructor.

    Arguments:
        device_factory: Callable    the device class
        name: str                   the name for ophyd
        prefix: str                 the PV prefix for the most (usually all) components
        wait: bool                  whether to run .wait_for_connection()
        fake: bool                  whether to fake with ophyd.sim
        post_create: Callable       (optional) a function to be run on the device after
                                    creation
        bl_prefix: bool             if true, add the beamline prefix when instantiating, if
                                    false the complete PV prefix must be supplied.
    Returns:
        The instance of the device.
    """
    already_existing_device: AnyDevice | None = ACTIVE_DEVICES.get(name)
    if fake:
        device_factory = cast(Callable[..., T], make_fake_device(device_factory))
    if already_existing_device is None:
        device_instance = device_factory(
            name=name,
            prefix=(
                f"{(BeamlinePrefix(BL).beamline_prefix)}{prefix}"
                if bl_prefix
                else prefix
            ),
            **kwargs,
        )
        ACTIVE_DEVICES[name] = device_instance
        if wait:
            wait_for_connection(device_instance, mock=fake)

    else:
        if not active_device_is_same_type(already_existing_device, device_factory):
            raise TypeError(
                f"Can't instantiate device of type {device_factory} with the same "
                f"name as an existing device. Device name '{name}' already used for "
                f"a(n) {type(already_existing_device)}."
            )
        device_instance = cast(T, already_existing_device)
    if post_create:
        post_create(device_instance)
    return device_instance


D = TypeVar("D", bound=OphydV2Device)
_skip = bool | Callable[[], bool]


class DeviceInitializationController(Generic[D]):
    def __init__(
        self,
        factory: Callable[[], D],
        eager_connect: bool,
        use_factory_name: bool,
        timeout: float,
        mock: bool,
        skip: _skip,
    ):
        self._factory: Callable[[], D] = factory
        self._cached_device: D | None = None
        self._eager_connect = eager_connect
        self._use_factory_name = use_factory_name
        self._timeout = timeout
        self._mock = mock
        self._skip = skip
        update_wrapper(self, factory)

    @property
    def skip(self) -> bool:
        return self._skip() if callable(self._skip) else self._skip

    @property
    def device(self) -> D | None:
        return self._cached_device

    def __call__(
        self,
        connect: bool | None = None,
        name: str | None = None,
        timeout: float | None = None,
        mock: bool | None = None,
    ) -> D:
        if self.device is not None:
            device = self.device
        else:
            device = self._factory()

        if name:
            device.set_name(name)
        elif not device.name and self._use_factory_name:
            device.set_name(self._factory.__name__)

        if connect or connect is None and self._eager_connect:
            call_in_bluesky_event_loop(
                device.connect(
                    timeout=timeout if timeout is not None else self._timeout,
                    mock=mock if mock is not None else self._mock,
                )
            )

        self._cache_device(device)
        return device

    def _cache_device(self, device: D):
        if device.name:
            ACTIVE_DEVICES[device.name] = device
        self._cached_device = device


def device_factory(
    *,
    eager_connect: Annotated[bool, "Connect or raise Exception at startup"] = True,
    use_factory_name: Annotated[bool, "Use factory name as name of device"] = True,
    timeout: Annotated[float, "Timeout for connecting to the device"] = DEFAULT_TIMEOUT,
    mock: Annotated[bool, "Use Signals with mock backends for device"] = False,
    skip: Annotated[
        _skip,
        "mark the factory to be (conditionally) skipped when beamline is imported by external program",
    ] = False,
) -> Callable[[Callable[[], D]], DeviceInitializationController[D]]:
    def decorator(factory: Callable[[], D]) -> DeviceInitializationController[D]:
        return DeviceInitializationController(
            factory, eager_connect, use_factory_name, timeout, mock, skip
        )

    return decorator


def set_path_provider(provider: UpdatingPathProvider):
    global PATH_PROVIDER

    PATH_PROVIDER = provider


def get_path_provider() -> UpdatingPathProvider:
    if PATH_PROVIDER is None:
        raise ValueError(
            "PathProvider has not been set! Ophyd-async StandardDetectors will not be able to write!"
        )
    return PATH_PROVIDER
