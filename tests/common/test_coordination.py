import uuid

import pytest

from dodal.common.coordination import group_uuid


@pytest.mark.parametrize("group", ["foo", "bar", "baz", str(uuid.uuid4())])
def test_group_uid(group: str):
    gid = group_uuid(group)
    assert gid.startswith(f"{group}-")
    assert not gid.endswith(f"{group}-")
