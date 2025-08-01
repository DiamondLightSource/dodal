from typing import Any

from deepdiff import DeepDiff

from dodal.devices.electron_analyser.abstract import AbstractBaseRegion


def assert_region_has_expected_values(
    r: AbstractBaseRegion, expected_region_values: dict[str, Any]
) -> None:
    actual_values = r.__dict__
    diff = DeepDiff(expected_region_values, actual_values)
    if diff:
        raise AssertionError(f"Region does not match expected values:\n{diff}")
    for key in expected_region_values.keys():
        assert actual_values.get(key) is not None
