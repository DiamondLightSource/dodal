import uuid
from inspect import Parameter, signature

import pytest
from bluesky.protocols import Movable

from dodal.common.coordination import group_uuid, inject
from dodal.common.types import MsgGenerator


@pytest.mark.parametrize("group", ["foo", "bar", "baz", str(uuid.uuid4())])
def test_group_uid(group: str):
    gid = group_uuid(group)
    assert gid.startswith(f"{group}-")
    assert not gid.endswith(f"{group}-")


def test_type_checking_ignores_inject():
    def example_function(x: Movable = inject("foo")) -> MsgGenerator:
        yield from {}

    # These asserts are sanity checks
    # the real test is whether this test passes type checking
    x: Parameter = signature(example_function).parameters["x"]
    assert x.annotation == Movable
    assert x.default == "foo"
