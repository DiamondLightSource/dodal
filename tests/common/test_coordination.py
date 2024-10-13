from inspect import Parameter, signature

import pytest
from bluesky.protocols import Movable
from bluesky.utils import MsgGenerator

from dodal.common.coordination import group_uuid, inject

static_uuid = "51aef931-33b4-4b33-b7ad-a8287f541202"


@pytest.mark.parametrize("group", ["foo", "bar", "baz", static_uuid])
def test_group_uid(group: str):
    gid = group_uuid(group)
    assert gid.startswith(f"{group}-")
    assert not gid.endswith(f"{group}-")


def test_type_checking_ignores_inject():
    def example_function(x: Movable = inject("foo")) -> MsgGenerator:  # noqa: B008
        yield from {}

    # These asserts are sanity checks
    # the real test is whether this test passes type checking
    x: Parameter = signature(example_function).parameters["x"]
    assert x.annotation == Movable
    assert x.default == "foo"
