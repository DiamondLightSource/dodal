import pytest

from dodal.common.beamlines.beamline_utils import (
    get_path_provider,
)
from dodal.devices.i11.mythen import Mythen3

# def test_mythen3_prepare(RE: RunEngine, mythen3: Mythen3):
#     def _inner_prepare(mythen3: Mythen3):
#         m = mythen3()
#         yield from bps.prepare(m)

#     RE(_inner_prepare(mythen3))


@pytest.fixture
async def connect_mythen() -> Mythen3:
    mythen = Mythen3(
        prefix="FOO-EA-DET-07:",
        path_provider=get_path_provider(),
        drv_suffix="DET",
        fileio_suffix="HDF:",
    )
    await mythen.connect(mock=True)

    return mythen
