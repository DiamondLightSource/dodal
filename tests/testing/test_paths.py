from pathlib import Path

import pytest

from dodal.testing.paths import is_path_banned

BANNED_PATHS = [Path("/dls"), Path("/dls_sw")]


@pytest.mark.parametrize(
    "path, expected_result",
    [
        (Path("/dls/iXX"), True),
        (Path("/dls_sw/iXX"), True),
        (Path("relative/path"), False),
        (Path("/absolute/path"), False),
    ],
)
def test_is_path_banned(path: Path, expected_result: bool) -> None:
    assert is_path_banned(path, BANNED_PATHS) is expected_result
