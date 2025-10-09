import asyncio
from inspect import Parameter, signature

import pytest
from bluesky.protocols import Movable
from bluesky.utils import MsgGenerator
from ophyd_async.epics.motor import Motor

from dodal.common.coordination import group_uuid, inject, locked
from dodal.testing import patch_motor

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


@pytest.mark.parametrize("state", [True, False])
async def test_device_locking(state: bool):
    async def is_unlocked() -> bool:
        return state

    mock_motor = locked(Motor(""), is_unlocked)
    await mock_motor.connect(mock=True)
    patch_motor(mock_motor)

    set_status = mock_motor.set(400)

    while not set_status.done:
        # Allow time for the set to be scheduled?
        await asyncio.sleep(0.01)

    new_location = await mock_motor.locate()
    assert new_location["readback"] == (400 if state else 0)
    assert new_location["setpoint"] == (400 if state else 0)


async def test_device_locked_raises_exception():
    async def is_unlocked() -> bool:
        return False

    mock_motor = locked(Motor(""), is_unlocked, ValueError("Unable!"))
    await mock_motor.connect(mock=True)

    with pytest.raises(ValueError, match="Unable!"):
        await mock_motor.set(400)
