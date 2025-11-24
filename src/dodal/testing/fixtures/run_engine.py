"""
Allow external repos to reuse these fixtures so defined in single place.
"""

import asyncio
import os
import threading
import time
from collections.abc import AsyncGenerator, Mapping

import pytest
import pytest_asyncio
from _pytest.fixtures import FixtureRequest
from bluesky.run_engine import RunEngine
from bluesky.simulators import RunEngineSimulator

_run_engine = RunEngine()

_ENABLE_FILEHANDLE_LEAK_CHECKS = (
    os.getenv("DODAL_ENABLE_FILEHANDLE_LEAK_CHECKS", "").lower() == "true"
)


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def _ensure_running_bluesky_event_loop(_global_run_engine):
    # make sure the event loop is thoroughly up and running before we try to create
    # any ophyd_async devices which might need it
    timeout = time.monotonic() + 1
    while not _global_run_engine.loop.is_running():
        await asyncio.sleep(0)
        if time.monotonic() > timeout:
            raise TimeoutError("This really shouldn't happen but just in case...")


@pytest.fixture()
async def run_engine(_global_run_engine: RunEngine) -> AsyncGenerator[RunEngine, None]:
    try:
        yield _global_run_engine
    finally:
        _global_run_engine.reset()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _global_run_engine() -> AsyncGenerator[RunEngine, None]:
    """
    Obtain a run engine, with its own event loop and thread.

    On closure of the scope, the run engine is stopped and the event loop closed
    in order to release all resources it consumes.
    """
    run_engine = RunEngine({}, call_returns_result=True)
    yield run_engine
    try:
        run_engine.halt()
    except Exception as e:
        # Ignore exception thrown if the run engine is already halted.
        print(f"Got exception while halting RunEngine {e}")
    finally:

        async def get_event_loop_thread():
            """Get the thread which the run engine created for the event loop."""
            return threading.current_thread()

        fut = asyncio.run_coroutine_threadsafe(get_event_loop_thread(), run_engine.loop)
        while not fut.done():
            # It's not clear why this is necessary, given we are
            # on a completely different thread and event loop
            # but without it our future never seems to be populated with a result
            # despite the coro getting executed
            await asyncio.sleep(0)
        # Terminate the event loop so that we can join() the thread
        run_engine.loop.call_soon_threadsafe(run_engine.loop.stop)
        run_engine_thread = fut.result()
        run_engine_thread.join()
        # This closes the filehandle in the event loop.
        # This cannot be called while the event loop is running
        run_engine.loop.close()
    del run_engine


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


@pytest.fixture(autouse=_ENABLE_FILEHANDLE_LEAK_CHECKS)
def check_for_filehandle_leaks(request: FixtureRequest):
    """
    Test fixture that can be enabled in order to check for leaked filehandles
    (typically caused by a rogue RunEngine instance).

    Note that this test is not enabled by default due to imposing a significant
    overhead. When a leak is suspected, usually from seeing a
    PytestUnraisableExceptionWarning, enable this via autouse and run the full
    test suite.
    """
    pid = os.getpid()
    _baseline_n_open_files = len(os.listdir(f"/proc/{pid}/fd"))
    try:
        yield
    finally:
        _n_open_files = len(os.listdir(f"/proc/{pid}/fd"))
        assert _n_open_files == _baseline_n_open_files, (
            f"Function {request.function.__name__} leaked some filehandles"
        )
