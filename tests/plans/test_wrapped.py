from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
from bluesky.run_engine import RunEngine
from event_model.documents import (
    DocumentType,
    EventDescriptor,
    RunStart,
    RunStop,
)
from ophyd_async.core import (
    DeviceCollector,
    PathProvider,
    StandardDetector,
)
from ophyd_async.sim.demo import PatternDetector
from pydantic import ValidationError

from dodal.plans.wrapped import count


@pytest.fixture
def det(RE: RunEngine, tmp_path: Path) -> StandardDetector:
    with DeviceCollector(mock=True):
        det = PatternDetector(tmp_path / "foo.h5")
    return det


@pytest.fixture
def path_provider(static_path_provider: PathProvider):
    # Prevents issue with leftover state from beamline tests
    with patch("dodal.plan_stubs.data_session.get_path_provider") as mock:
        mock.return_value = static_path_provider
        yield


def test_count_delay_validation(det: StandardDetector, path_provider, RE):
    with pytest.raises(
        AssertionError, match="Number of delays given must be 2: was given [1]"
    ):
        RE(count({det}, num=3, delay=[1]))
    with pytest.raises(
        AssertionError,
        match="Number of delays given must be 2: was given [1,2,3,4,5,6]",
    ):
        RE(count({det}, num=3, delay=[1, 2, 3, 4, 5, 6]))


def test_count_validates_counting_something(path_provider, RE):
    with pytest.raises(
        ValidationError, match="Set should have at least 1 item after validation, not 0"
    ):
        RE(count(set()))


def test_count_physical_delay(det: StandardDetector, path_provider, RE):
    with pytest.raises(
        ValidationError, match="Input should be greater than or equal to 0"
    ):
        RE(count({det}, delay=-1.0))


def test_count_sensible_num(det: StandardDetector, path_provider, RE):
    with pytest.raises(
        ValidationError, match="Input should be greater than or equal to 1"
    ):
        RE(count({det}, num=-1))
    with pytest.raises(
        ValidationError, match="Input should be greater than or equal to 1"
    ):
        RE(count({det}, num=0))


def test_count_output(det: StandardDetector, path_provider, RE):
    docs: dict[str, list[DocumentType]] = {}
    RE(
        count({det}),
        lambda name, doc: docs.setdefault(name, []).append(doc),
    )

    for metadata_doc in ("start", "stop", "descriptor"):
        assert metadata_doc in docs
        assert len(docs[metadata_doc]) == 1

    start = cast(RunStart, docs["start"][0])
    assert (hints := start.get("hints")) and (
        hints.get("dimensions") == [(("time",), "primary")]
    )
    assert start.get("shape") == (1,)

    descriptor = cast(EventDescriptor, docs["descriptor"][0])
    assert det.name in descriptor.get("object_keys", {})

    stop = cast(RunStop, docs["stop"][0])
    assert stop.get("exit_status") == "success"
    assert stop.get("num_events") == {"primary": 1}
    assert stop.get("run_start") == start.get("uid")

    # Check that dets are all triggered
    assert "stream_resource" in docs
    assert len(docs["stream_resource"]) == 2  # det, det.sum

    assert "stream_datum" in docs
    assert len(docs["stream_datum"]) == 1 * 2  # each point per resource


def test_multi_count_output(det: StandardDetector, path_provider, RE):
    docs: dict[str, list[DocumentType]] = {}
    RE(
        count({det}, num=3),
        lambda name, doc: docs.setdefault(name, []).append(doc),
    )

    for metadata_doc in ("start", "stop", "descriptor"):
        assert metadata_doc in docs
        assert len(docs[metadata_doc]) == 1

    start = cast(RunStart, docs["start"][0])
    assert (hints := start.get("hints")) and (
        hints.get("dimensions") == [(("time",), "primary")]
    )
    assert start.get("shape") == (3,)

    descriptor = cast(EventDescriptor, docs["descriptor"][0])
    assert det.name in descriptor.get("object_keys", {})

    stop = cast(RunStop, docs["stop"][0])
    assert stop.get("exit_status") == "success"
    assert stop.get("num_events") == {"primary": 3}
    assert stop.get("run_start") == start.get("uid")

    # Check that dets are all triggered
    assert "stream_resource" in docs
    assert len(docs["stream_resource"]) == 2  # det, det.sum

    assert "stream_datum" in docs
    assert len(docs["stream_datum"]) == 3 * 2  # each point per resource
