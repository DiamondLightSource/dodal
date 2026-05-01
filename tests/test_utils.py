import os
from unittest.mock import MagicMock, patch

import pytest

from dodal.beamlines import i04, i23
from dodal.utils import (
    _find_next_run_number_from_files,
    get_beamline_based_on_environment_variable,
    get_beamline_name,
    get_hostname,
    get_run_number,
)


def test_get_hostname() -> None:
    with patch("dodal.utils.socket.gethostname") as mock:
        mock.return_value = "a.b.c"
        assert get_hostname() == "a"


@pytest.mark.parametrize("bl", ["", "$%^&*", "nonexistent"])
def test_invalid_beamline_variable_causes_get_device_module_to_raise(bl):
    with patch.dict(os.environ, {"BEAMLINE": bl}), pytest.raises(ValueError):
        get_beamline_based_on_environment_variable()


@pytest.mark.parametrize("bl,module", [("i04", i04), ("i23", i23)])
def test_valid_beamline_variable_causes_get_device_module_to_return_module(bl, module):
    with patch.dict(os.environ, {"BEAMLINE": bl}):
        assert get_beamline_based_on_environment_variable() == module


def test_find_next_run_number_from_files_gets_correct_number():
    assert (
        _find_next_run_number_from_files(
            ["V31-1-x0093_1.nxs", "V31-1-x0093_2.nxs", "V31-1-x0093_265.nxs"]
        )
        == 266
    )


@patch("dodal.log.LOGGER.warning")
def test_find_next_run_number_gives_warning_with_wrong_nexus_names(
    mock_logger: MagicMock,
):
    assert (
        _find_next_run_number_from_files(
            ["V31-1-x0093.nxs", "eggs", "V31-1-x0093_1.nxs"]
        )
        == 2
    )
    assert mock_logger.call_count == 2


@patch("os.listdir")
@patch("dodal.utils._find_next_run_number_from_files")
def test_get_run_number_finds_all_nexus_files(
    mock_find_next_run_number: MagicMock, mock_list_dir: MagicMock
):
    files = ["blah.nxs", "foo", "bar.nxs", "ham.h5"]
    mock_list_dir.return_value = files
    get_run_number("dir")
    mock_find_next_run_number.assert_called_once_with(["blah.nxs", "bar.nxs"])


@patch("os.listdir")
def test_if_nexus_files_are_unnumbered_then_return_one(
    mock_list_dir: MagicMock,
):
    assert _find_next_run_number_from_files(["file.nxs", "foo.nxs", "ham.nxs"]) == 1


@patch("os.listdir")
@patch("dodal.utils._find_next_run_number_from_files")
def test_run_number_1_given_on_first_nexus_file(
    mock_find_next_run_number: MagicMock, mock_list_dir: MagicMock
):
    files = ["blah", "foo", "bar"]
    mock_list_dir.return_value = files
    assert get_run_number("dir") == 1
    mock_find_next_run_number.assert_not_called()


@patch("os.listdir")
def test_get_run_number_uses_prefix(mock_list_dir: MagicMock):
    foos = (f"foo_{i}.nxs" for i in range(4))
    bars = (f"bar_{i}.nxs" for i in range(7))
    bazs = (f"baz_{i}.nxs" for i in range(23, 29))
    files = [*foos, *bars, *bazs]
    mock_list_dir.return_value = files
    assert get_run_number("dir", "foo") == 4
    assert get_run_number("dir", "bar") == 7
    assert get_run_number("dir", "baz") == 29
    assert get_run_number("dir", "qux") == 1


def test_get_beamline_name_raises_error_if_environment_variable_not_set_and_no_default_given(
    monkeypatch,
):
    monkeypatch.delenv("BEAMLINE", raising=False)
    with pytest.raises(ValueError):
        get_beamline_name()
