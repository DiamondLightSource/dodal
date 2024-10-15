from types import ModuleType
from unittest.mock import Mock, patch

from dodal.common.beamlines.controller_utils import make_all_controlled_devices


def test_make_all_controlled_devices_import_module():
    # Test the case where `module` is a string, and we expect it to be imported
    with patch("dodal.common.beamlines.controller_utils.import_module") as mock_import:
        mock_module = Mock(spec=ModuleType)
        mock_import.return_value = mock_module

        devices, exceptions = make_all_controlled_devices(module="test_module")

        mock_import.assert_called_once_with("test_module")
        assert isinstance(devices, dict)
        assert isinstance(exceptions, dict)
