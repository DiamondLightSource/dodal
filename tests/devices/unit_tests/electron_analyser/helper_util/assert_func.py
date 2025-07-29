from typing import Any

from dodal.devices.electron_analyser.abstract import AbstractBaseRegion


def assert_region_has_expected_values(
    r: AbstractBaseRegion, expected_region_values: dict[str, Any]
) -> None:
    for key in r.__dict__:
        if key in expected_region_values:
            assert r.__dict__[key] == expected_region_values[key]
        else:
            raise KeyError('key "' + key + '" is not in the expected values.')

    for key in expected_region_values.keys():
        assert r.__dict__.get(key) is not None
