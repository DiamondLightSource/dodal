from pathlib import Path

import pytest

from dodal.testing.paths import is_path_banned


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
    assert is_path_banned(path) is expected_result
