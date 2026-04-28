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
