from collections.abc import Sequence
from typing import cast

import pytest
from bluesky.protocols import Readable
from bluesky.run_engine import RunEngine
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
from pydantic import ValidationError

from dodal.plans.wrapped import count


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


def test_count_delay_validation(det: StandardDetector, RE):
    args: dict[float | Sequence[float], str] = {  # type: ignore
        # List wrong length
        (1,): "Number of delays given must be 2: was given 1",
        (1, 2, 3): "Number of delays given must be 2: was given 3",
        # Delay non-physical
        # negative time
        -1: "Input should be greater than or equal to 0",
        (-1, 2): "Input should be greater than or equal to 0",
        # # null time
        None: "Input should be a valid number",
        (None, 2): "Input should be a valid number",
        # # NaN time
        "foo": "Input should be a valid number",
        ("foo", 2): "Input should be a valid number",
    }
    for delay, reason in args.items():
        with pytest.raises((ValidationError, AssertionError), match=reason):
            RE(count({det}, num=3, delay=delay))
        print(delay)


def test_count_detectors_validation(RE):
    args: dict[str, set[Readable]] = {
        # No device to read
        "Set should have at least 1 item after validation, not 0": set(),
        # Not Readable
        "Input should be an instance of Readable": set("foo"),  # type: ignore
    }
    for reason, dets in args.items():
        with pytest.raises(ValidationError, match=reason):
            RE(count(dets))


def test_count_num_validation(det: StandardDetector, RE):
    args: dict[int, str] = {
        -1: "Input should be greater than or equal to 1",
        0: "Input should be greater than or equal to 1",
        "str": "Input should be a valid integer",  # type: ignore
    }
    for num, reason in args.items():
        with pytest.raises(ValidationError, match=reason):
            RE(count({det}, num=num))


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
    assert (hints := start.get("hints")) and (
        hints.get("dimensions") == [(("time",), "primary")]
    )


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


@pytest.mark.parametrize("documents_from_num", [1, 3], indirect=True)
def test_plan_produces_expected_resources(
    documents_from_num: dict[str, list[DocumentType]],
    det: StandardDetector,
):
    docs = documents_from_num.get("stream_resource")
    data_keys = [det.name, f"{det.name}-sum"]
    assert docs and len(docs) == len(data_keys)
    for i in range(len(docs)):
        resource = cast(StreamResource, docs[i])
        assert resource.get("data_key") == data_keys[i]


@pytest.mark.parametrize(
    "documents_from_num, length", ([1, 1], [3, 3]), indirect=["documents_from_num"]
)
def test_plan_produces_expected_datums(
    documents_from_num: dict[str, list[DocumentType]],
    length: int,
    det: StandardDetector,
):
    docs = documents_from_num.get("stream_datum")
    data_keys = [det.name, f"{det.name}-sum"]
    assert docs and len(docs) == len(data_keys) * length
