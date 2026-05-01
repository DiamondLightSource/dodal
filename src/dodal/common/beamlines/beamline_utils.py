import inspect
from collections.abc import Callable
from typing import TypeVar

from daq_config_server import ConfigClient
from ophyd_async.core import (
    PathProvider,
)

from dodal.log import LOGGER
from dodal.utils import (
    AnyDevice,
)

BL = ""


def set_beamline(beamline: str):
    global BL
    BL = beamline


def active_device_is_same_type(
    active_device: AnyDevice, device: Callable[..., AnyDevice]
) -> bool:
    return inspect.isclass(device) and isinstance(active_device, device)


T = TypeVar("T", bound=AnyDevice)


def set_path_provider(provider: PathProvider):
    global PATH_PROVIDER

    LOGGER.info(
        "Setting global path provider to %s (previously %s)",
        provider,
        globals().get("PATH_PROVIDER"),
    )
    PATH_PROVIDER = provider


def get_path_provider() -> PathProvider:
    return PATH_PROVIDER


def clear_path_provider() -> None:
    global PATH_PROVIDER
    LOGGER.info("Clearing global path provider: %s", globals().get("PATH_PROVIDER"))
    try:
        del PATH_PROVIDER
    except NameError:
        # In this case the path provider was never set so we can do nothing
        pass


def set_config_client(config_client: ConfigClient):
    global CONFIG_CLIENT

    LOGGER.info(
        f"Setting global config client to {config_client} (previously {globals().get('CONFIG_CLIENT')})",
    )
    CONFIG_CLIENT = config_client


def get_config_client() -> ConfigClient:
    return CONFIG_CLIENT


def clear_config_client() -> None:
    global CONFIG_CLIENT
    LOGGER.info(f"Clearing global config client: {globals().get('CONFIG_CLIENT')}")
    try:
        del CONFIG_CLIENT
    except NameError:
        # In this case the config client was never set so we can do nothing
        pass
