from pathlib import Path

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    PathInfo,
    PathProvider,
)

from dodal.beamlines import i03
from dodal.common.beamlines.beamline_utils import clear_devices
from dodal.common.visit import (
    DirectoryServiceClientBase,
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.devices.util.test_utils import patch_motor

PATH_INFO_FOR_TESTING: PathInfo = PathInfo(
    directory_path=Path("/does/not/exist"),
    filename="on_this_filesystem",
)


@pytest.fixture
def dummy_visit_client() -> DirectoryServiceClientBase:
    return LocalDirectoryServiceClient()


@pytest.fixture
def static_path_provider(
    tmp_path: Path, dummy_visit_client: DirectoryServiceClientBase
) -> PathProvider:
    return StaticVisitPathProvider(
        beamline="ixx", root=tmp_path, client=dummy_visit_client
    )


@pytest.fixture
def smargon(RE: RunEngine):
    smargon = i03.smargon(fake_with_ophyd_sim=True)

    for motor in [smargon.omega, smargon.x, smargon.y, smargon.z]:
        patch_motor(motor)

    yield smargon

    clear_devices()
