from collections.abc import Sequence
from functools import reduce
from typing import cast

import pytest
from bluesky.run_engine import RunEngine
from event_model.documents import (
    DocumentType,
    Event,
    EventDescriptor,
    RunStart,
    RunStop,
    StreamResource,
)
from ophyd_async.core import StandardDetector
from ophyd_async.sim import SimMotor
from scanspec.specs import Line

from dodal.plans import spec_scan


@pytest.fixture
def documents_from_expected_shape(
    request: pytest.FixtureRequest,
    det: StandardDetector,
    RE: RunEngine,
    x_axis: SimMotor,
    y_axis: SimMotor,
) -> dict[str, list[DocumentType]]:
    shape: Sequence[int] = request.param
    motors = [x_axis, y_axis]
    # Does not support static, https://github.com/bluesky/scanspec/issues/154
    # spec = Static.duration(1)
    spec = Line(motors[0], 0, 5, shape[0])
    for i in range(1, len(shape)):
        spec = spec * Line(motors[i], 0, 5, shape[i])

    docs: dict[str, list[DocumentType]] = {}
    RE(
        spec_scan({det}, spec),  # type: ignore
        lambda name, doc: docs.setdefault(name, []).append(doc),
    )
    return docs


spec_and_shape = (
    # Does not support static, https://github.com/bluesky/scanspec/issues/154
    # [(), (1,)],  # static
    [(1,), (1,)],
    [(3,), (3,)],
    [(1, 1), (1, 1)],
    [(3, 3), (3, 3)],
)


def length_from_shape(shape: tuple[int, ...]) -> int:
    return reduce(lambda x, y: x * y, shape)


@pytest.mark.parametrize(
    "documents_from_expected_shape, shape",
    spec_and_shape,
    indirect=["documents_from_expected_shape"],
)
def test_plan_produces_expected_start_document(
    documents_from_expected_shape: dict[str, list[DocumentType]],
    shape: tuple[int, ...],
    x_axis: SimMotor,
    y_axis: SimMotor,
):
    axes = len(shape)
    expected_data_keys = (
        [
            x_axis.hints.get("fields", [])[0],
            y_axis.hints.get("fields", [])[0],
        ]
        if axes == 2
        else [x_axis.hints.get("fields", [])[0]]
    )
    dimensions = [([data_key], "primary") for data_key in expected_data_keys]
    docs = documents_from_expected_shape.get("start")
    assert docs and len(docs) == 1
    start = cast(RunStart, docs[0])
    assert start.get("shape") == shape
    assert (hints := start.get("hints"))
    for dimension in dimensions:
        assert dimension in hints.get("dimensions")  # type: ignore


@pytest.mark.parametrize(
    "documents_from_expected_shape, shape",
    spec_and_shape,
    indirect=["documents_from_expected_shape"],
)
def test_plan_produces_expected_stop_document(
    documents_from_expected_shape: dict[str, list[DocumentType]], shape: tuple[int, ...]
):
    docs = documents_from_expected_shape.get("stop")
    assert docs and len(docs) == 1
    stop = cast(RunStop, docs[0])
    assert stop.get("num_events") == {"primary": length_from_shape(shape)}
    assert stop.get("exit_status") == "success"


@pytest.mark.parametrize(
    "documents_from_expected_shape, shape",
    spec_and_shape,
    indirect=["documents_from_expected_shape"],
)
def test_plan_produces_expected_descriptor(
    documents_from_expected_shape: dict[str, list[DocumentType]],
    det: StandardDetector,
    shape: tuple[int, ...],
):
    docs = documents_from_expected_shape.get("descriptor")
    assert docs and len(docs) == 1
    descriptor = cast(EventDescriptor, docs[0])
    object_keys = descriptor.get("object_keys")
    assert object_keys is not None and det.name in object_keys
    assert descriptor.get("name") == "primary"


@pytest.mark.parametrize(
    "documents_from_expected_shape, shape",
    spec_and_shape,
    indirect=["documents_from_expected_shape"],
)
def test_plan_produces_expected_events(
    documents_from_expected_shape: dict[str, list[DocumentType]],
    shape: tuple[int, ...],
    det: StandardDetector,
    x_axis: SimMotor,
    y_axis: SimMotor,
):
    axes = len(shape)
    expected_data_keys = (
        {
            x_axis.hints.get("fields", [])[0],
            y_axis.hints.get("fields", [])[0],
        }
        if axes == 2
        else {x_axis.hints.get("fields", [])[0]}
    )
    docs = documents_from_expected_shape.get("event")
    assert docs and len(docs) == length_from_shape(shape)
    for i in range(len(docs)):
        event = cast(Event, docs[i])
        assert len(event.get("data")) == axes
        assert event.get("data").keys() == expected_data_keys
        assert event.get("seq_num") == i + 1


@pytest.mark.parametrize(
    "documents_from_expected_shape, shape",
    spec_and_shape,
    indirect=["documents_from_expected_shape"],
)
def test_plan_produces_expected_resources(
    documents_from_expected_shape: dict[str, list[DocumentType]],
    shape: tuple[int, ...],
    det: StandardDetector,
):
    docs = documents_from_expected_shape.get("stream_resource")
    data_keys = [det.name, f"{det.name}-sum"]
    assert docs and len(docs) == len(data_keys)
    for i in range(len(docs)):
        resource = cast(StreamResource, docs[i])
        assert resource.get("data_key") == data_keys[i]


@pytest.mark.parametrize(
    "documents_from_expected_shape, shape",
    spec_and_shape,
    indirect=["documents_from_expected_shape"],
)
def test_plan_produces_expected_datums(
    documents_from_expected_shape: dict[str, list[DocumentType]],
    shape: tuple[int, ...],
    det: StandardDetector,
):
    docs = documents_from_expected_shape.get("stream_datum")
    data_keys = [det.name, f"{det.name}-sum"]
    assert docs and len(docs) == len(data_keys) * length_from_shape(shape)
