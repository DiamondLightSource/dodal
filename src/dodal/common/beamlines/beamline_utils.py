from daq_config_server.client import ConfigClient
from ophyd_async.core import (
    PathProvider,
)

from dodal.log import LOGGER

BL = ""

PATH_PROVIDER_DEFAULT = ""
PATH_PROVIDER_PANDA = "panda"
PATH_PROVIDER_EIGER = "eiger"

_path_providers: dict[str, PathProvider] = {}


def set_beamline(beamline: str):
    global BL
    BL = beamline


def set_path_provider(provider: PathProvider, key: str = PATH_PROVIDER_DEFAULT):
    """Register a path provider for the specified key.

    Args:
        provider: The path provider to register
        key: A key identifying the path provider if unspecified the default provider is set.
    """
    global _path_providers

    LOGGER.info(
        "Setting global path provider to %s (previously %s)",
        provider,
        _path_providers.get(key),
    )
    _path_providers[key] = provider


def get_path_provider(key: str = PATH_PROVIDER_DEFAULT) -> PathProvider:
    """Fetch the specified path provider.

    Args:
        key: A key identifying the path provider to fetch, or if unspecified return the default provider.

    Raises:
        KeyError: if the specified provider cannot be found
    """
    return _path_providers[key]


def clear_path_provider(key: str = PATH_PROVIDER_DEFAULT) -> None:
    """Unregister the specified path provider
    Args:
        key: The key identifying the path provider, or the default provider if unspecified.
    """
    global _path_providers
    LOGGER.info("Clearing global path provider: %s", _path_providers.get(key))
    try:
        del _path_providers[key]
    except KeyError:
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
