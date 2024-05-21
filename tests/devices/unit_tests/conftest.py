from pathlib import Path

import pytest
from ophyd_async.core import DirectoryInfo, DirectoryProvider, StaticDirectoryProvider

from dodal.testing_utils import *  # noqa: F403

DIRECTORY_INFO_FOR_TESTING: DirectoryInfo = DirectoryInfo(
    root=Path("/does/not/exist"),
    resource_dir=Path("/on/this/filesystem"),
)


@pytest.fixture
def static_directory_provider(tmp_path: Path) -> DirectoryProvider:
    return StaticDirectoryProvider(tmp_path)
