import os

import pytest
from bluesky import RunEngine

_baseline = None  # module-level storage for first run


@pytest.mark.parametrize("iteration", range(5))
def test_run_engine_has_no_memory_leak(run_engine: RunEngine, iteration: int) -> None:
    global _baseline
    pid = os.getpid()
    open_files = len(os.listdir(f"/proc/{pid}/fd"))
    if iteration == 0:
        _baseline = open_files
    else:
        try:
            assert _baseline == open_files
        except AssertionError as exc:
            raise AssertionError(
                "Detected memeory leak, the number of open files has increased from "
                f"{_baseline} to {open_files} when calling the run_engine fixture",
            ) from exc
