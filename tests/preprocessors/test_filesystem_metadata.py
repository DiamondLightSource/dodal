from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import bluesky.plan_stubs as bps
import bluesky.plans as bp
import pytest
from aiohttp import ClientResponseError
from bluesky import RunEngine
from bluesky.preprocessors import (
    run_decorator,
    run_wrapper,
    set_run_key_decorator,
    set_run_key_wrapper,
    stage_wrapper,
)
from bluesky.protocols import (
    HasName,
    Readable,
    Reading,
    Status,
    Triggerable,
)
from bluesky.run_engine import RunEngine
from event_model.documents.event_descriptor import DataKey
from ophyd.status import StatusBase
from ophyd_async.core import DeviceCollector, DirectoryProvider
from pydantic import BaseModel

from dodal.common.types import MsgGenerator, UpdatingDirectoryProvider
from dodal.common.visit import (
    DataCollectionIdentifier,
    DirectoryServiceClientBase,
    LocalDirectoryServiceClient,
    StaticVisitDirectoryProvider,
)
from dodal.plans.data_session_metadata import (
    DATA_SESSION,
    attach_data_session_metadata_wrapper,
)


class FakeDetector(Readable, HasName, Triggerable):
    _name: str
    _provider: DirectoryProvider

    def __init__(
        self,
        name: str,
        provider: DirectoryProvider,
    ) -> None:
        self._name = name
        self._provider = provider

    async def read(self) -> dict[str, Reading]:
        return {
            f"{self.name}_data": {
                "value": "test",
                "timestamp": 0.0,
            },
        }

    async def describe(self) -> dict[str, DataKey]:
        directory_info = self._provider()
        source = str(
            directory_info.root
            / directory_info.resource_dir
            / f"{directory_info.prefix}{self.name}{directory_info.suffix}.h5"
        )
        return {
            f"{self.name}_data": {
                "dtype": "string",
                "shape": [1],
                "source": source,
            }
        }

    def trigger(self) -> Status:
        status = StatusBase()
        status.set_finished()
        return status

    @property
    def name(self) -> str:
        return self._name

    @property
    def parent(self) -> None:
        return None


class MockDirectoryServiceClient(LocalDirectoryServiceClient):
    def __init__(self):
        self.fail = False
        super().__init__()

    async def create_new_collection(self) -> DataCollectionIdentifier:
        if self.fail:
            raise ClientResponseError(None, ())  # type: ignore

        return await super().create_new_collection()

    async def get_current_collection(self) -> DataCollectionIdentifier:
        if self.fail:
            raise ClientResponseError(None, ())  # type: ignore

        return await super().get_current_collection()


class DataEvent(BaseModel):
    name: str
    doc: Any


@pytest.fixture
def client() -> DirectoryServiceClientBase:
    return MockDirectoryServiceClient()


@pytest.fixture
def provider(
    client: DirectoryServiceClientBase, tmp_path: Path
) -> UpdatingDirectoryProvider:
    return StaticVisitDirectoryProvider("example", tmp_path, client=client)


@pytest.fixture(params=[1, 2])
def detectors(request, provider: UpdatingDirectoryProvider) -> list[Readable]:
    number_of_detectors = request.param
    with DeviceCollector(mock=True):
        dets: list[Readable] = [
            FakeDetector(name=f"det{i}", provider=provider)
            for i in range(number_of_detectors)
        ]
    return dets


def simple_run(detectors: list[Readable]) -> MsgGenerator:
    yield from bp.count(detectors)


def multi_run(detectors: list[Readable]) -> MsgGenerator:
    yield from bp.count(detectors)
    yield from bp.count(detectors)


def multi_nested_plan(detectors: list[Readable]) -> MsgGenerator:
    yield from simple_run(detectors)
    yield from simple_run(detectors)


def multi_run_single_stage(detectors: list[Readable]) -> MsgGenerator:
    def stageless_count() -> MsgGenerator:
        return (yield from bps.one_shot(detectors))

    def inner_plan() -> MsgGenerator:
        yield from run_wrapper(stageless_count())
        yield from run_wrapper(stageless_count())

    yield from stage_wrapper(inner_plan(), detectors)


def multi_run_single_stage_multi_group(
    detectors: list[Readable],
) -> MsgGenerator:
    def stageless_count() -> MsgGenerator:
        return (yield from bps.one_shot(detectors))

    def inner_plan() -> MsgGenerator:
        yield from run_wrapper(stageless_count(), md={DATA_SESSION: 1})
        yield from run_wrapper(stageless_count(), md={DATA_SESSION: 1})
        yield from run_wrapper(stageless_count(), md={DATA_SESSION: 2})
        yield from run_wrapper(stageless_count(), md={DATA_SESSION: 2})

    yield from stage_wrapper(inner_plan(), detectors)


@run_decorator(md={DATA_SESSION: 12345})
@set_run_key_decorator("outer")
def nested_run_with_metadata(detectors: list[Readable]) -> MsgGenerator:
    yield from set_run_key_wrapper(bp.count(detectors), "inner")
    yield from set_run_key_wrapper(bp.count(detectors), "inner")


@run_decorator()
@set_run_key_decorator("outer")
def nested_run_without_metadata(
    detectors: list[Readable],
) -> MsgGenerator:
    yield from set_run_key_wrapper(bp.count(detectors), "inner")
    yield from set_run_key_wrapper(bp.count(detectors), "inner")


def test_simple_run_gets_scan_number(
    RE: RunEngine,
    detectors: list[Readable],
    provider: UpdatingDirectoryProvider,
    tmp_path: Path,
) -> None:
    docs = collect_docs(
        RE,
        simple_run(detectors),
        provider,
    )
    assert docs[0].name == "start"
    assert docs[0].doc[DATA_SESSION] == "example-1"
    assert_all_detectors_used_collection_numbers(tmp_path, docs, detectors, ["1"])


@pytest.mark.parametrize("plan", [multi_run, multi_nested_plan])
def test_multi_run_gets_scan_numbers(
    RE: RunEngine,
    detectors: list[Readable],
    plan: Callable[[list[Readable]], MsgGenerator],
    provider: UpdatingDirectoryProvider,
    tmp_path: Path,
) -> None:
    """Test is here to demonstrate that multi run plans will overwrite files."""
    docs = collect_docs(
        RE,
        plan(detectors),
        provider,
    )
    start_docs = find_start_docs(docs)
    assert len(start_docs) == 2
    assert start_docs[0].doc[DATA_SESSION] == "example-1"
    assert start_docs[1].doc[DATA_SESSION] == "example-1"
    assert_all_detectors_used_collection_numbers(tmp_path, docs, detectors, ["1", "1"])


def test_multi_run_single_stage(
    RE: RunEngine,
    detectors: list[Readable],
    provider: UpdatingDirectoryProvider,
    tmp_path: Path,
) -> None:
    docs = collect_docs(
        RE,
        multi_run_single_stage(detectors),
        provider,
    )
    start_docs = find_start_docs(docs)
    assert len(start_docs) == 2
    assert start_docs[0].doc[DATA_SESSION] == "example-1"
    assert start_docs[1].doc[DATA_SESSION] == "example-1"
    assert_all_detectors_used_collection_numbers(
        tmp_path,
        docs,
        detectors,
        [
            "1",
            "1",
        ],
    )


def test_multi_run_single_stage_multi_group(
    RE: RunEngine,
    detectors: list[Readable],
    provider: UpdatingDirectoryProvider,
    tmp_path: Path,
) -> None:
    docs = collect_docs(
        RE,
        multi_run_single_stage_multi_group(detectors),
        provider,
    )
    start_docs = find_start_docs(docs)
    assert len(start_docs) == 4
    assert start_docs[0].doc[DATA_SESSION] == "example-1"
    assert start_docs[1].doc[DATA_SESSION] == "example-1"
    assert start_docs[2].doc[DATA_SESSION] == "example-1"
    assert start_docs[3].doc[DATA_SESSION] == "example-1"
    assert_all_detectors_used_collection_numbers(
        tmp_path,
        docs,
        detectors,
        ["1", "1", "1", "1"],
    )


def test_nested_run_with_metadata(
    RE: RunEngine,
    detectors: list[Readable],
    provider: UpdatingDirectoryProvider,
    tmp_path: Path,
) -> None:
    """Test is here to demonstrate that nested runs will be treated as a single run.

    That means detectors in such runs will overwrite files.
    """
    docs = collect_docs(
        RE,
        nested_run_with_metadata(detectors),
        provider,
    )
    start_docs = find_start_docs(docs)
    assert len(start_docs) == 3
    assert start_docs[0].doc[DATA_SESSION] == "example-1"
    assert start_docs[1].doc[DATA_SESSION] == "example-1"
    assert start_docs[2].doc[DATA_SESSION] == "example-1"
    assert_all_detectors_used_collection_numbers(tmp_path, docs, detectors, ["1", "1"])


def test_nested_run_without_metadata(
    RE: RunEngine,
    detectors: list[Readable],
    provider: UpdatingDirectoryProvider,
    tmp_path: Path,
) -> None:
    """Test is here to demonstrate that nested runs will be treated as a single run.

    That means detectors in such runs will overwrite files.
    """
    docs = collect_docs(
        RE,
        nested_run_without_metadata(detectors),
        provider,
    )
    start_docs = find_start_docs(docs)
    assert len(start_docs) == 3
    assert start_docs[0].doc[DATA_SESSION] == "example-1"
    assert start_docs[1].doc[DATA_SESSION] == "example-1"
    assert start_docs[2].doc[DATA_SESSION] == "example-1"
    assert_all_detectors_used_collection_numbers(tmp_path, docs, detectors, ["1", "1"])


def test_visit_directory_provider_fails(
    RE: RunEngine,
    detectors: list[Readable],
    provider: UpdatingDirectoryProvider,
    client: MockDirectoryServiceClient,
) -> None:
    client.fail = True
    with pytest.raises(ValueError):
        collect_docs(
            RE,
            simple_run(detectors),
            provider,
        )


def test_visit_directory_provider_fails_after_one_sucess(
    RE: RunEngine,
    detectors: list[Readable],
    provider: UpdatingDirectoryProvider,
    client: MockDirectoryServiceClient,
) -> None:
    collect_docs(
        RE,
        simple_run(detectors),
        provider,
    )
    client.fail = True
    with pytest.raises(ValueError):
        collect_docs(
            RE,
            simple_run(detectors),
            provider,
        )


def collect_docs(
    RE: RunEngine,
    plan: MsgGenerator,
    provider: UpdatingDirectoryProvider,
) -> list[DataEvent]:
    events = []

    def on_event(name: str, doc: Mapping[str, Any]) -> None:
        events.append(DataEvent(name=name, doc=doc))

    wrapped_plan = attach_data_session_metadata_wrapper(plan, provider)
    RE(wrapped_plan, on_event)
    return events


def assert_all_detectors_used_collection_numbers(
    tmp_path: Path,
    docs: list[DataEvent],
    detectors: list[Readable],
    dataCollectionIds: list[str],
) -> None:
    descriptors = find_descriptor_docs(docs)
    assert len(descriptors) == len(dataCollectionIds)

    for descriptor, dataCollectionId in zip(
        descriptors, dataCollectionIds, strict=False
    ):
        for detector in detectors:
            source = descriptor.doc.get("data_keys", {}).get(f"{detector.name}_data")[
                "source"
            ]
            expected_source = f"example-{dataCollectionId}-{detector.name}.h5"
            assert Path(source) == tmp_path / expected_source


def find_start_docs(docs: list[DataEvent]) -> list[DataEvent]:
    return list(filter(lambda event: event.name == "start", docs))


def find_descriptor_docs(docs: list[DataEvent]) -> list[DataEvent]:
    return list(filter(lambda event: event.name == "descriptor", docs))
