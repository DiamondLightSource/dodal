import pytest

from dodal.common.coordination import group_uuid

static_uuid = "51aef931-33b4-4b33-b7ad-a8287f541202"


@pytest.mark.parametrize("group", ["foo", "bar", "baz", static_uuid])
def test_group_uid(group: str):
    gid = group_uuid(group)
    assert gid.startswith(f"{group}-")
    assert not gid.endswith(f"{group}-")
