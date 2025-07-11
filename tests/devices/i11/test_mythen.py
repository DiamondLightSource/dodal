import bluesky.plan_stubs as bps
from bluesky.run_engine import RunEngine

from dodal.devices.i11.mythen import Mythen3


def test_mythen3_prepare(RE: RunEngine, mythen3: Mythen3):
    def _inner_prepare(mythen3: Mythen3):
        yield from bps.prepare(mythen3)

    RE(_inner_prepare(mythen3))
