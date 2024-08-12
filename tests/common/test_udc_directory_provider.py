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
async def test_udc_directory_provider_after_update(initial, tmp_path):
    provider = PandASubdirectoryProvider(initial)
    await provider.update(directory=tmp_path)
    directory_info = provider()
    assert directory_info.root == tmp_path
    assert directory_info.resource_dir == Path("panda")


async def test_udc_directory_provider_no_suffix():
    initial = Path("initial")
    provider = PandASubdirectoryProvider(initial)
    root_path = Path("/tmp/my_data")
    await provider.update(directory=root_path)
    directory_info = provider()
    assert directory_info.root == root_path
    assert directory_info.resource_dir == Path("panda")
    assert directory_info.suffix == ""


async def test_udc_directory_provider_with_suffix():
    initial = Path("initial")
    provider = PandASubdirectoryProvider(initial)
    root_path = Path("/tmp/my_data")
    await provider.update(directory=root_path, suffix="_123")
    directory_info = provider()
    assert directory_info.root == root_path
    assert directory_info.resource_dir == Path("panda")
    assert directory_info.suffix == "_123"


async def test_udc_directory_provider_creates_subdirectory_if_not_exists(tmp_path):
    root = tmp_path
    subdir = root / Path("panda")
    assert not subdir.exists()
    provider = PandASubdirectoryProvider(Path("initial"))
    await provider.update(directory=root)
    assert subdir.exists()
