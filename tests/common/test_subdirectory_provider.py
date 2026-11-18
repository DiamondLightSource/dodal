import re
from pathlib import Path

import pytest

from dodal.common.subdirectory_provider import SubdirectoryPathProvider


def test_path_provider_fails_if_update_not_called_beforehand():
    provider = SubdirectoryPathProvider("bl1")
    with pytest.raises(
        AssertionError,
        match=re.escape("Directory unknown, update() must be called at least once"),
    ):
        provider()


def test_subdirectory_path_provider():
    provider = SubdirectoryPathProvider("i19-1", Path("/tmp/dls/i19-1/data/cm12345-1"))
    path_info = provider()
    assert path_info.directory_path == Path("/tmp/dls/i19-1/data/cm12345-1")
    assert path_info.filename.startswith("i19-1")


async def test_update_path_provider(tmp_path):
    provider = SubdirectoryPathProvider("i19-2")
    subdir_path = tmp_path / "test_dir"
    subdir_path.mkdir()
    await provider.update(directory=tmp_path, subdirectory="test_dir", prefix="test_01")
    path_info = provider()
    assert path_info.directory_path == subdir_path
    assert path_info.filename == "test_01"
