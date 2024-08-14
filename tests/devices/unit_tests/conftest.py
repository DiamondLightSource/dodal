from pathlib import Path

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DirectoryInfo,
    DirectoryProvider,
    StaticDirectoryProvider,
)

from dodal.beamlines import i03
from dodal.common.beamlines.beamline_utils import clear_devices
from dodal.devices.util.test_utils import patch_motor

DIRECTORY_INFO_FOR_TESTING: DirectoryInfo = DirectoryInfo(
    root=Path("/does/not/exist"),
    resource_dir=Path("/on/this/filesystem"),
)


@pytest.fixture
def static_directory_provider(tmp_path: Path) -> DirectoryProvider:
    return StaticDirectoryProvider(tmp_path)


@pytest.fixture
def smargon(RE: RunEngine):
    smargon = i03.smargon(fake_with_ophyd_sim=True)

    for motor in [smargon.omega, smargon.x, smargon.y, smargon.z]:
        patch_motor(motor)

    yield smargon

    clear_devices()
