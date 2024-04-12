import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from bluesky.utils import new_uid
from ophyd_async.core import DeviceCollector, StaticDirectoryProvider, set_sim_value
from pathlib import Path
from dodal.devices.areadetector.pimteAD import HDFStatsPimte

@pytest.fixture
def tmp_directory_provider(tmp_path: Path) -> StaticDirectoryProvider:
    return StaticDirectoryProvider(tmp_path)

def count_sim(det: HDFStatsPimte, times: int = 1):
    """Test plan to do the equivalent of bp.count for a sim detector."""

    yield from bps.stage_all(det)
    yield from bps.open_run()
    yield from bps.declare_stream(det, name="primary", collect=False)
    for _ in range(times):
        read_value = yield from bps.rd(det._writer.hdf.num_captured)
        yield from bps.trigger(det, wait=False, group="wait_for_trigger")

        yield from bps.sleep(0.001)
        set_sim_value(det._writer.hdf.num_captured, read_value + 1)

        yield from bps.wait(group="wait_for_trigger")
        yield from bps.create()
        yield from bps.read(det)
        yield from bps.save()

    yield from bps.close_run()
    yield from bps.unstage_all(det)


@pytest.fixture
async def single_detector(RE: RunEngine, tmp_directory_provider: StaticDirectoryProvider) -> HDFStatsPimte:
    async with DeviceCollector(sim=True):
        detector = HDFStatsPimte(prefix, tmp_directory_provider, "pimte")
    set_sim_value(detector._controller.driver.array_size_x, 10)
    set_sim_value(detector._controller.driver.array_size_y, 20)
    set_sim_value(detector.hdf.file_path_exists, True)
    set_sim_value(detector._writer.hdf.num_captured, 0)
    return detector


async def test_pimte(RE: RunEngine, single_detector: HDFStatsPimte):
    names = []
    docs = []
    RE.subscribe(lambda name, _: names.append(name))
    RE.subscribe(lambda _, doc: docs.append(doc))

    RE(count_sim(single_detector))
    writer = single_detector._writer

    assert (
        await writer.hdf.file_path.get_value()
        == writer._directory_provider().root.as_posix()
    )

    assert names == [
        "start",
        "descriptor",
        "stream_resource",
        "stream_resource",
        "stream_datum",
        "stream_datum",
        "event",
        "stop",
    ]
