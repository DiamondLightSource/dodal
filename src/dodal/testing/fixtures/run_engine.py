"""
Allow external repos to reuse these fixtures so defined in single place.
"""

import asyncio
import time
from collections.abc import Mapping

import pytest
from bluesky.run_engine import RunEngine
from bluesky.simulators import RunEngineSimulator


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


@pytest.fixture
def sim_run_engine() -> RunEngineSimulator:
    return RunEngineSimulator()


@pytest.fixture
def run_engine_documents(run_engine: RunEngine) -> Mapping[str, list[dict]]:
    docs: dict[str, list[dict]] = {}

    def append_and_print(name, doc):
        if name not in docs:
            docs[name] = []
        docs[name] += [doc]

    run_engine.subscribe(append_and_print)
    return docs
