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
        _baseline_n_open_files = n_open_files
    else:
        if _baseline_n_open_files is None:
            raise Exception(
                "Unable to determine number of file handlers as it is None."
            )
        try:
            delta = n_open_files - _baseline_n_open_files
            # Allow a small threshold from other processes e.g from pytest itself.
            assert delta < threshold
        except AssertionError as exc:
            raise AssertionError(
                "Detected file handle leak, the number of open files has increased from "
                f"{_baseline_n_open_files} to {n_open_files} when calling the "
                "run_engine fixture",
            ) from exc
