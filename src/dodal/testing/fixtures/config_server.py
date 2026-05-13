import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar
from unittest.mock import patch

import pytest
from daq_config_server.models import ConfigModel
from pydantic import TypeAdapter

T = TypeVar("T", str, dict, ConfigModel)


def fake_config_server_get_file_contents(
    filepath: str | Path,
    desired_return_type: type[T] = str,
    reset_cached_result: bool = True,
    force_parser: Callable[[str], Any] | None = None,
) -> T:
    """Fakes getting a file from the config server by reading it directly.

    Args:
        filepath (str | Path): Filepath of the file to read
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
    filepath = Path(filepath)
    # Minimal logic required for unit tests
    with filepath.open("r") as f:
        contents = f.read()
    if force_parser:
        return TypeAdapter(desired_return_type).validate_python(force_parser(contents))
    if desired_return_type is str:
        return contents  # type: ignore
    if desired_return_type is dict:
        return json.loads(contents)
    if issubclass(desired_return_type, ConfigModel):
        return desired_return_type.model_validate(json.loads(contents))
    raise ValueError("Invalid return type requested")


@pytest.fixture(autouse=True)
def mock_config_server():
    # Don't actually talk to central service during unit tests, and reset caches between test

    with patch(
        "daq_config_server.app.client.ConfigClient.get_file_contents",
        side_effect=fake_config_server_get_file_contents,
    ):
        yield
