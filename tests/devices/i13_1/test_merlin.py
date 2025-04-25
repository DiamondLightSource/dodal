from typing import cast

import pytest
from event_model import StreamDatum, StreamResource
from ophyd_async.core import (
    DetectorTrigger,
    PathProvider,
    TriggerInfo,
    init_devices,
)
from ophyd_async.testing import set_mock_value

from dodal.devices.i13_1.merlin import Merlin


@pytest.fixture
def one_shot_trigger_info() -> TriggerInfo:
    return TriggerInfo(
        exposure_timeout=None,
        number_of_events=1,
        trigger=DetectorTrigger.INTERNAL,
        deadtime=0.0,
        livetime=None,
    )


@pytest.fixture
async def merlin(static_path_provider: PathProvider) -> Merlin:
    async with init_devices(mock=True):
        merlin = Merlin(
            prefix="BL13J-EA-DET-04",
            # name="merlin",
            # drv_suffix="CAM:",
            # fileio_suffix="HDF5:",
            path_provider=static_path_provider,
        )

    return merlin


async def test_trigger(
    merlin: Merlin,
    one_shot_trigger_info: TriggerInfo,
):
    set_mock_value(merlin.hdf.file_path_exists, True)

    await merlin.stage()
    await merlin.prepare(one_shot_trigger_info)
    await merlin._controller.arm()

    assert await merlin.drv.acquire.get_value()

    await merlin._controller.wait_for_idle()


async def test_can_collect(
    merlin: Merlin,
    static_path_provider: PathProvider,
    one_shot_trigger_info: TriggerInfo,
):
    set_mock_value(merlin.hdf.file_path_exists, True)
    set_mock_value(merlin.drv.array_size_x, 10)
    set_mock_value(merlin.drv.array_size_y, 20)
    set_mock_value(merlin.hdf.num_frames_chunks, 1)
    set_mock_value(merlin.hdf.full_file_name, "/foo/bar.hdf")

    await merlin.stage()
    await merlin.prepare(one_shot_trigger_info)
    docs = [(name, doc) async for name, doc in merlin.collect_asset_docs(1)]
    assert len(docs) == 2
    assert docs[0][0] == "stream_resource"
    stream_resource = cast(StreamResource, docs[0][1])

    sr_uid = stream_resource["uid"]
    assert stream_resource["data_key"] == "merlin"
    assert stream_resource["uri"] == "file://localhost/foo/bar.hdf"
    assert stream_resource["parameters"] == {
        "dataset": "/entry/data/data",
        "chunk_shape": (1, 20, 10),
    }
    assert docs[1][0] == "stream_datum"
    stream_datum = cast(StreamDatum, docs[1][1])
    assert stream_datum["stream_resource"] == sr_uid
    assert stream_datum["seq_nums"] == {"start": 0, "stop": 0}
    assert stream_datum["indices"] == {"start": 0, "stop": 1}


async def test_can_decribe_collect(merlin: Merlin, one_shot_trigger_info: TriggerInfo):
    set_mock_value(merlin.hdf.file_path_exists, True)
    set_mock_value(merlin.drv.array_size_x, 10)
    set_mock_value(merlin.drv.array_size_y, 20)

    assert (await merlin.describe_collect()) == {}
    await merlin.stage()
    await merlin.prepare(one_shot_trigger_info)
    assert (await merlin.describe_collect()) == {
        "merlin": {
            "source": "mock+ca://BL13J-EA-DET-04HDF5:FullFileName_RBV",
            "shape": [1, 20, 10],
            "dtype": "array",
            "dtype_numpy": "|i1",
            "external": "STREAM:",
        }
    }
