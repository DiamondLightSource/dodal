from pathlib import Path

import pytest

from dodal.common.udc_directory_provider import UDCDirectoryProvider


@pytest.mark.parametrize(
    "root, expected",
    [
        [Path("/foo"), Path("/foo/panda")],
        [
            Path("/tmp/dls/i03/data/2024/cm31105-4/xraycentring/123456/"),
            Path("/tmp/dls/i03/data/2024/cm31105-4/xraycentring/123456/panda"),
        ],
    ],
)
def test_udc_directory_provider_get_and_set(root, expected):
    provider = UDCDirectoryProvider(root)
    directory_info = provider()
    assert directory_info.root == root
    assert directory_info.root.joinpath(directory_info.resource_dir) == expected
