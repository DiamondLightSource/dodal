from typing import Any

from dodal.devices.electron_analyser.base_region import TBaseRegion


def check_region_model_list_to_expected_values(
    regions: list[TBaseRegion], expected_values: list[dict[str, Any]]
) -> None:
    for i, r in enumerate(regions):
        for key in r.__dict__:
            if key in expected_values[i]:
                assert r.__dict__[key] == expected_values[i][key]
            else:
                raise KeyError('key "' + key + '" is not in the expected values.')


def is_list_of_custom_type(value, custom_type: type) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, custom_type) for item in value
    )
