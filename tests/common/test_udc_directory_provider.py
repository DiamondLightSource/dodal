import re
from pathlib import Path

import pytest

from dodal.common.udc_directory_provider import PandASubdirectoryProvider


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
    provider = PandASubdirectoryProvider(root)
    directory_info = provider()
    assert directory_info.root == root
    assert directory_info.root.joinpath(directory_info.resource_dir) == expected


def test_udc_directory_provider_excepts_before_update():
    provider = PandASubdirectoryProvider()
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Directory unknown for PandA to write into, update() needs to be called at least once"
        ),
    ):
        provider()


@pytest.mark.parametrize(
    "initial",
    [Path("."), None],
)
def test_udc_directory_provider_after_update(initial, tmp_path):
    provider = PandASubdirectoryProvider(initial)
    provider.update(tmp_path)
    directory_info = provider()
    assert directory_info.root == tmp_path
    assert directory_info.resource_dir == Path("panda")
