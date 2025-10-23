"""
Allow external repos to reuse these fixtures so defined in single place.
"""

import asyncio
import time
from collections.abc import Mapping
from pathlib import Path

import pytest
from bluesky.run_engine import RunEngine
from ophyd.status import Status
from ophyd_async.core import (
    PathProvider,
)

from dodal.common.visit import DirectoryServiceClient, StaticVisitPathProvider


@pytest.fixture
async def static_path_provider(
    tmp_path: Path, dummy_visit_client: DirectoryServiceClient
) -> PathProvider:
    svpp = StaticVisitPathProvider(
        beamline="ixx", root=tmp_path, client=dummy_visit_client
    )
    await svpp.update()
    return svpp


@pytest.fixture
def run_engine_documents(run_engine: RunEngine) -> Mapping[str, list[dict]]:
    docs: dict[str, list[dict]] = {}

    def append_and_print(name, doc):
        if name not in docs:
            docs[name] = []
        docs[name] += [doc]

    run_engine.subscribe(append_and_print)
    return docs


def failed_status(failure: Exception) -> Status:
    status = Status()
    status.set_exception(failure)
    return status


@pytest.fixture(scope="session", autouse=True)
async def _ensure_running_bluesky_event_loop():
    run_engine = RunEngine()
    # make sure the event loop is thoroughly up and running before we try to create
    # any ophyd_async devices which might need it
    timeout = time.monotonic() + 1
    while not run_engine.loop.is_running():
        await asyncio.sleep(0)
        if time.monotonic() > timeout:
            raise TimeoutError("This really shouldn't happen but just in case...")


@pytest.fixture()
async def run_engine():
    yield RunEngine()
