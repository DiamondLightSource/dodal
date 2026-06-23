import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar
from unittest.mock import MagicMock

import pytest
from daq_config_server import ConfigClient
from daq_config_server.models import ConfigModel
from pydantic import TypeAdapter

from dodal.testing.paths import is_path_banned

T = TypeVar("T", str, dict, ConfigModel)

TModel = TypeVar("TModel", bound=ConfigModel)

# Test can register a specific file path with an assoicated file contents to model
# conversion function.
MOCK_CONFIG_CLIENT_PATH_TO_MODEL_CONVERSION: dict[
    str, Callable[[str], ConfigModel]
] = {}


def mock_config_server_get_file_contents(
    file_path: str | Path,
    desired_return_type: type[T] = str,
    reset_cached_result: bool = True,
    force_parser: Callable[[str], Any] | None = None,
) -> T:
    """Mocks getting a file from the config server by reading it directly.

    Args:
        file_path (str | Path): Filepath of the file to read
        desired_return_type (type[T], optional): Type to convert the file to. Defaults to str.
        reset_cached_result (bool, optional): Whether or not to use the config server's cached result.
            Does nothing here as we don't cache. Defaults to True.
        force_parser (Callable[[str], Any] | None, optional): Use a certain converter function.
            Only needed for the interim where the converter exists but the config server has not
            been redeployed. Defaults to None.

    Raises:
        ValueError: Raised if an invalid type is requested

    Returns:
        T: The contents of the config file.
    """
    requested_path = Path(file_path)
    if requested_path.is_absolute():
        if is_path_banned(requested_path):
            raise AssertionError(
                f"Attempt to open {requested_path} from inside a unit test"
            )
    # Minimal logic required for unit tests
    with requested_path.open("r") as f:
        contents = f.read()
    if force_parser:
        return TypeAdapter(desired_return_type).validate_python(force_parser(contents))
    if desired_return_type is str:
        return contents  # type: ignore
    if desired_return_type is dict:
        return json.loads(contents)
    if issubclass(desired_return_type, ConfigModel):
        if str(requested_path) in MOCK_CONFIG_CLIENT_PATH_TO_MODEL_CONVERSION:
            callable = MOCK_CONFIG_CLIENT_PATH_TO_MODEL_CONVERSION[str(requested_path)]
            return callable(contents)  # type: ignore
        return desired_return_type.model_validate(json.loads(contents))
    raise ValueError("Invalid return type requested")


# ToDo - Add documentation for tests to reuse this fixture.
@pytest.fixture
def mock_config_client() -> ConfigClient:
    # Don't actually talk to central service during unit tests, and reset caches between test
    mock_config_client = ConfigClient()
    mock_config_client.get_file_contents = MagicMock(spec=["get_file_contents"])

    mock_config_client.get_file_contents.side_effect = (
        mock_config_server_get_file_contents
    )
    return mock_config_client
