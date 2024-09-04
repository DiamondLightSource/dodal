import re
from pathlib import Path

import pytest

from dodal.common.udc_directory_provider import PandASubpathProvider


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
def test_udc_path_provider_get_and_set(root, expected):
    provider = PandASubpathProvider(root)
    directory_info = provider()
    assert directory_info.directory_path == expected


def test_udc_path_provider_excepts_before_update():
    provider = PandASubpathProvider()
    with pytest.raises(
        AssertionError,
        match=re.escape(
            "Directory unknown for PandA to write into, update() needs to be called at least once"
        ),
    ):
        provider()


@pytest.mark.parametrize(
    "initial",
    [Path("."), None],
)
async def test_udc_path_provider_after_update(initial, tmp_path):
    provider = PandASubpathProvider(initial)
    await provider.update(directory=tmp_path)
    directory_info = provider()
    assert directory_info.directory_path == tmp_path / "panda"


async def test_udc_path_provider_no_suffix(tmp_path):
    initial = Path("initial")
    provider = PandASubpathProvider(initial)
    root_path = tmp_path / "my_data"
    root_path.mkdir()
    await provider.update(directory=root_path)
    directory_info = provider()
    assert directory_info.directory_path == root_path / "panda"


async def test_udc_path_provider_with_suffix(tmp_path):
    initial = Path("initial")
    provider = PandASubpathProvider(initial)
    root_path = tmp_path / "my_data"
    root_path.mkdir()
    await provider.update(directory=root_path, suffix="_123")
    directory_info = provider()
    assert directory_info.directory_path == root_path / "panda"
    assert directory_info.filename.endswith("_123")
