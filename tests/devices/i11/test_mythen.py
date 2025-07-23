import pytest

# from ophyd_async.testing import set_mock_value
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
async def test_mythen() -> Mythen3:
    mythen = Mythen3(
        prefix="BL11I-EA-DET-07:",
        path_provider=get_path_provider(),
        drv_suffix="DET",
        fileio_suffix="HDF:",
    )
    await mythen.connect(mock=True)

    # set_mock_value(mythen.x_mm.user_readback, x)

    return mythen
