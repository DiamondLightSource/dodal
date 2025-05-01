from collections.abc import Generator
from typing import cast

import pytest
from bluesky.run_engine import RunEngine
from event_model import StreamDatum
from event_model.documents import (
    DocumentType,
    Event,
    EventDescriptor,
    RunStart,
    RunStop,
    StreamResource,
)
from ophyd_async.core import (
    StandardDetector,
)

from dodal.beamlines import adsim
from dodal.devices.adsim import SimStage
from dodal.plans import count


@pytest.fixture
def det(RE) -> Generator[StandardDetector]:
    yield adsim.det(connect_immediately=True)
    adsim.det.cache_clear()


@pytest.fixture
def sim_stage(RE) -> Generator[SimStage]:
    yield adsim.stage(connect_immediately=True)
    adsim.stage.cache_clear()


@pytest.fixture
def documents_from_num(
    request: pytest.FixtureRequest, det: StandardDetector, RE: RunEngine
) -> dict[str, list[DocumentType]]:
    docs: dict[str, list[DocumentType]] = {}
    RE(
        count({det}, num=request.param),
        lambda name, doc: docs.setdefault(name, []).append(doc),
    )
    return docs


@pytest.mark.adsim
@pytest.mark.parametrize(
    "documents_from_num, shape", ([1, (1,)], [3, (3,)]), indirect=["documents_from_num"]
)
def test_plan_produces_expected_start_document(
    documents_from_num: dict[str, list[DocumentType]], shape: tuple[int, ...]
):
    docs = documents_from_num.get("start")
    assert docs and len(docs) == 1
    start = cast(RunStart, docs[0])
    assert start.get("shape") == shape
    assert start.get("plan_name") == "count"
    assert start.get("detectors") == ["det"]
    assert start.get("num_points") == shape[0]
    assert start.get("num_intervals") == shape[0] - 1
    assert cast(str, start.get("data_session")).startswith("adsim")

    assert (hints := start.get("hints")) and (
        hints.get("dimensions") == [(("time",), "primary")]
    )


@pytest.mark.adsim
@pytest.mark.parametrize(
    "documents_from_num, length", ([1, 1], [3, 3]), indirect=["documents_from_num"]
)
def test_plan_produces_expected_stop_document(
    documents_from_num: dict[str, list[DocumentType]], length: int
):
    docs = documents_from_num.get("stop")
    assert docs and len(docs) == 1
    stop = cast(RunStop, docs[0])
    assert stop.get("num_events") == {"primary": length}
    assert stop.get("exit_status") == "success"


@pytest.mark.adsim
@pytest.mark.parametrize("documents_from_num", [1], indirect=True)
def test_plan_produces_expected_descriptor(
    documents_from_num: dict[str, list[DocumentType]], det: StandardDetector
):
    docs = documents_from_num.get("descriptor")
    assert docs and len(docs) == 1
    descriptor = cast(EventDescriptor, docs[0])
    object_keys = descriptor.get("object_keys")
    assert object_keys is not None and det.name in object_keys
    assert descriptor.get("name") == "primary"


@pytest.mark.adsim
@pytest.mark.parametrize(
    "documents_from_num, length", ([1, 1], [3, 3]), indirect=["documents_from_num"]
)
def test_plan_produces_expected_events(
    documents_from_num: dict[str, list[DocumentType]],
    length: int,
    det: StandardDetector,
):
    docs = documents_from_num.get("event")
    assert docs and len(docs) == length
    for i in range(len(docs)):
        event = cast(Event, docs[i])
        assert not event.get("data")  # empty data
        assert event.get("seq_num") == i + 1


@pytest.mark.adsim
@pytest.mark.parametrize("documents_from_num", [1, 3], indirect=True)
def test_plan_produces_expected_resources(
    documents_from_num: dict[str, list[DocumentType]],
    det: StandardDetector,
):
    docs = documents_from_num.get("stream_resource")
    data_keys = [det.name]
    assert docs and len(docs) == len(data_keys)
    for i in range(len(docs)):
        resource = cast(StreamResource, docs[i])
        assert resource.get("data_key") == data_keys[i]
        assert resource.get("mimetype") == "application/x-hdf5"
        assert resource.get("parameters") == {
            "dataset": "/entry/data/data",
            "swmr": False,
            "multiplier": 1,
            "chunk_shape": (1, 1024, 1024),
        }


@pytest.mark.adsim
@pytest.mark.parametrize(
    "documents_from_num, length", ([1, 1], [3, 3]), indirect=["documents_from_num"]
)
def test_plan_produces_expected_datums(
    documents_from_num: dict[str, list[DocumentType]],
    length: int,
    det: StandardDetector,
):
    docs = cast(list[StreamDatum], documents_from_num.get("stream_datum"))
    data_keys = [det.name]  # If we enable e.g. Stats plugin add to this
    assert (
        docs and len(docs) <= len(data_keys) * length
    )  # at most 1 stream_datum per point
    descriptor = docs[0].get("descriptor")
    assert all(
        doc.get("descriptor") == descriptor for doc in docs
    )  # all docs in one stream
    assert len({doc.get("uid") for doc in docs}) == len(docs)  # all docs unique uid

    def docs_for_stream(data_key: str):
        stream_resource = [
            resource
            for resource in cast(
                list[StreamResource], documents_from_num.get("stream_resource")
            )
            if resource.get("data_key") == data_key
        ][0]
        return [
            doc
            for doc in docs
            if doc.get("stream_resource") == stream_resource.get("uid")
        ]

    def assert_all_seq_nums_accounted(data_key_docs: list[StreamDatum]):
        doc_starts = [doc.get("seq_nums").get("start") for doc in data_key_docs]
        doc_stops = [doc.get("seq_nums").get("stop") for doc in data_key_docs]
        assert doc_starts.pop(0) == 1  # start at 1
        assert doc_stops.pop() == length + 1  # end at length
        assert all(
            doc_stop in doc_starts for doc_stop in doc_stops
        )  # each range is adjacent

    for data_key in data_keys:
        data_key_docs = docs_for_stream(data_key)
        assert_all_seq_nums_accounted(data_key_docs)
        stream_resource = data_key_docs[0].get(
            "stream_resource"
        )  # each data_key uses a consistent resource
        assert all(
            doc.get("stream_resource") == stream_resource for doc in data_key_docs
        )
