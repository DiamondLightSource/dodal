import os
from collections.abc import Generator
from typing import cast
from unittest.mock import patch

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
    PathProvider,
    StandardDetector,
    StaticPathProvider,
    UUIDFilenameProvider,
)

from dodal.beamlines import adsim
from dodal.common.beamlines.beamline_utils import clear_path_provider, set_path_provider
from dodal.devices.motors import XThetaStage
from dodal.plans import count

"""
System tests that can be run against the containerised IOCs from epics-containers:
https://github.com/epics-containers/example-services

Check out that repository and using docker or podman deploy the services in the compose
file:

```sh
docker compose up -d
```

Run these system tests, with your EPICS environment configured to talk to the gateways:
```sh
python -m pytest -m 'requires(instrument="adsim")'
```

"""


@pytest.fixture(scope="module", autouse=True)
def with_env():
    with patch.dict(
        os.environ,
        {
            "EPICS_CA_NAME_SERVERS": "127.0.0.1:5094",
            "EPICS_PVA_NAME_SERVERS": "127.0.0.1:5095",
            "EPICS_CA_ADDR_LIST": "127.0.0.1:5094",
        },
        clear=True,
    ):
        yield


@pytest.fixture
def path_provider() -> Generator[PathProvider]:
    # path must be available to the `det` container, so cannot use tmp_path
    path_provider = StaticPathProvider(UUIDFilenameProvider(), "/tmp")
    set_path_provider(path_provider)
    yield path_provider
    clear_path_provider()


@pytest.fixture
def det(RE, path_provider: PathProvider) -> Generator[StandardDetector]:
    yield adsim.det(connect_immediately=True)
    adsim.det.cache_clear()


@pytest.fixture
def sim_stage(RE) -> Generator[XThetaStage]:
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


@pytest.mark.requires(instrument="adsim")
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

    assert (hints := start.get("hints")) and (
        hints.get("dimensions") == [(("time",), "primary")]
    )


@pytest.mark.requires(instrument="adsim")
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


@pytest.mark.requires(instrument="adsim")
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


@pytest.mark.requires(instrument="adsim")
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


@pytest.mark.requires(instrument="adsim")
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
            "chunk_shape": (1, 1024, 1024),
        }


@pytest.mark.requires(instrument="adsim")
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
