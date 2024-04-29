from pathlib import Path

import pytest

from dodal.common.udc_directory_provider import (
    get_udc_directory_provider,
    set_directory,
)


@pytest.mark.parametrize(
    "root, expected",
    [
        ["/foo", "/foo/panda"],
        [
            "/tmp/dls/i03/data/2024/cm31105-4/xraycentring/123456/",
            "/tmp/dls/i03/data/2024/cm31105-4/xraycentring/123456/panda",
        ],
    ],
)
def test_udc_directory_provider_get_and_set(root, expected):
    path = Path(root)
    set_directory(path)
    directory_info = get_udc_directory_provider()()
    assert directory_info.root == path
    assert str(directory_info.root.joinpath(directory_info.resource_dir)) == expected
