import json
from pathlib import Path
from typing import Any

from daq_config_server.client import ConfigServer
from daq_config_server.models import (
    ConfigModel,
)

from .mock_oav_config import MockOavConfig


class MockConfigServer(ConfigServer):
    def get_file_contents(
        self,
        file_path: str | Path,
        desired_return_type: type[Any] = str,
        reset_cached_result: bool = False,
    ) -> Any:
        print()
        if str(file_path).endswith("display.configuration"):
            return MockOavConfig.get_display_config()
        elif str(file_path).endswith("jCameraManZoomLevels.xml"):
            return MockOavConfig.get_zoom_params_file()
        elif str(file_path).endswith("OAVCentring.json"):
            return MockOavConfig.get_oav_config_json()
        else:
            return self._fake_config_server_read(
                file_path, desired_return_type, reset_cached_result
            )

    def _fake_config_server_read(
        self,
        filepath: str | Path,
        desired_return_type: type[str] | type[dict] | ConfigModel = str,
        reset_cached_result: bool = False,
    ) -> Any:
        filepath = Path(filepath)
        # Minimal logic required for unit tests
        with filepath.open("r") as f:
            contents = f.read()
            if desired_return_type is str:
                return contents
            elif desired_return_type is dict:
                return json.loads(contents)
            elif issubclass(desired_return_type, ConfigModel):  # type: ignore
                return desired_return_type.model_validate(json.loads(contents))
