import os

import pytest
from bluesky import RunEngine

_baseline_n_open_files = None
threshold = 5


@pytest.mark.parametrize("iteration", range(11))
def test_run_engine_fixture_has_no_file_handler_leak(
    run_engine: RunEngine, iteration: int
) -> None:
    global _baseline_n_open_files
    pid = os.getpid()
    n_open_files = len(os.listdir(f"/proc/{pid}/fd"))
    if iteration == 0:
        _baseline_n_open_files = n_open_files + 1
    else:
        try:
            delta = _baseline_n_open_files == n_open_files
            # Allow a small threshold from other processes e.g from pytest itself.
            assert delta < threshold
        except AssertionError as exc:
            raise AssertionError(
                "Detected memeory leak, the number of open files has increased from "
                f"{_baseline_n_open_files} to {n_open_files} when calling the "
                "run_engine fixture",
            ) from exc
