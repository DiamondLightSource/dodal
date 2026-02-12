import json
from pathlib import Path
from typing import TypeVar
from unittest.mock import patch

import pytest
from daq_config_server.models import ConfigModel

T = TypeVar("T", str, dict, ConfigModel)


def fake_config_server_get_file_contents(
    filepath: str | Path,
    desired_return_type: type[T] = str,
    reset_cached_result: bool = True,
) -> T:
    filepath = Path(filepath)
    # Minimal logic required for unit tests
    with filepath.open("r") as f:
        contents = f.read()
    if desired_return_type is str:
        return contents  # type: ignore
    elif desired_return_type is dict:
        return json.loads(contents)
    elif issubclass(desired_return_type, ConfigModel):
        return desired_return_type.model_validate(json.loads(contents))
    raise ValueError("Invalid return type requested")


@pytest.fixture(autouse=True)
def mock_config_server():
    # Don't actually talk to central service during unit tests, and reset caches between test

    with patch(
        "daq_config_server.client.ConfigServer.get_file_contents",
        side_effect=fake_config_server_get_file_contents,
    ):
        yield
