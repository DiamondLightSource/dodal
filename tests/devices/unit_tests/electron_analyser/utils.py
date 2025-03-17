from typing import Any

from dodal.devices.electron_analyser.base_region import TBaseRegion

TEST_DATA_PATH = "tests/test_data/electron_analyser/"


def check_region_model_list_to_expected_values(
    regions: list[TBaseRegion], expected_values: list[dict[str, Any]]
) -> None:
    for i, r in enumerate(regions):
        for key in r.__dict__:
            if key in expected_values[i]:
                assert r.__dict__[key] == expected_values[i][key]
            else:
                raise KeyError('key "' + key + '" is not in the expected values.')
