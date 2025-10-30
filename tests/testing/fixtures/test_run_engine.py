import os

import pytest
from bluesky import RunEngine

_baseline_n_open_files = None  # module-level storage for first run


@pytest.mark.parametrize("iteration", range(5))
def test_run_engine_fixture_has_no_memory_leak(
    run_engine: RunEngine, iteration: int
) -> None:
    global _baseline_n_open_files
    pid = os.getpid()
    n_open_files = len(os.listdir(f"/proc/{pid}/fd"))
    if iteration == 0:
        _baseline_n_open_files = n_open_files
    else:
        try:
            assert _baseline_n_open_files == n_open_files
        except AssertionError as exc:
            raise AssertionError(
                "Detected memeory leak, the number of open files has increased from "
                f"{_baseline_n_open_files} to {n_open_files} when calling the "
                "run_engine fixture",
            ) from exc
