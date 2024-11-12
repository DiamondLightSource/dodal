from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
from bluesky.run_engine import RunEngine
from event_model.documents import (
    DocumentType,
    Event,
    EventDescriptor,
    RunStart,
    RunStop,
)
from ophyd_async.core import (
    DeviceCollector,
    PathProvider,
    StandardDetector,
)
from ophyd_async.sim.demo import PatternDetector, SimMotor
from scanspec.specs import Line

from dodal.plans import spec_scan


@pytest.fixture
def det(RE: RunEngine, tmp_path: Path) -> StandardDetector:
    with DeviceCollector(mock=True):
        det = PatternDetector(tmp_path / "foo.h5")
    return det


@pytest.fixture
def x_axis(RE: RunEngine) -> SimMotor:
    with DeviceCollector(mock=True):
        x_axis = SimMotor()
    return x_axis


@pytest.fixture
def y_axis(RE: RunEngine) -> SimMotor:
    with DeviceCollector(mock=True):
        y_axis = SimMotor()
    return y_axis


@pytest.fixture
def path_provider(static_path_provider: PathProvider):
    # Prevents issue with leftover state from beamline tests
    with patch("dodal.plan_stubs.data_session.get_path_provider") as mock:
        mock.return_value = static_path_provider
        yield


def test_output_of_simple_spec(
    RE: RunEngine, x_axis: SimMotor, det: StandardDetector, path_provider
):
    docs: dict[str, list[DocumentType]] = {}
    RE(
        spec_scan(
            {det},
            Line(axis=x_axis, start=1, stop=2, num=3),
        ),
        lambda name, doc: docs.setdefault(name, []).append(doc),
    )
    for metadata_doc in ("start", "stop", "descriptor"):
        assert metadata_doc in docs
        assert len(docs[metadata_doc]) == 1

    start = cast(RunStart, docs["start"][0])
    assert (hints := start.get("hints")) and (
        hints.get("dimensions") == [([x_axis.user_readback.name], "primary")]
    )
    assert start.get("shape") == (3,)

    descriptor = cast(EventDescriptor, docs["descriptor"][0])
    assert x_axis.name in descriptor.get("object_keys", {})
    assert det.name in descriptor.get("object_keys", {})

    stop = cast(RunStop, docs["stop"][0])
    assert stop.get("exit_status") == "success"
    assert stop.get("num_events") == {"primary": 3}
    assert stop.get("run_start") == start.get("uid")

    assert "event" in docs

    initial_position = 1.0
    step = 0.5
    for doc, index in zip(docs["event"], range(1, 4), strict=True):
        event = cast(Event, doc)
        location = initial_position + ((index - 1) * step)
        assert event.get("data").get(x_axis.user_readback.name) == location

    # Output of detector not linked to Spec, just check that dets are all triggered
    assert "stream_resource" in docs
    assert len(docs["stream_resource"]) == 2  # det, det.sum

    assert "stream_datum" in docs
    assert len(docs["stream_datum"]) == 3 * 2  # each point per resource
