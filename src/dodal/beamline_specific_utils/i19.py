from collections.abc import Awaitable, Callable
from enum import Enum

from dodal.devices.i19.hutch_access import HutchAccessControl


class HutchState(str, Enum):
    EH1 = "EH1"
    EH2 = "EH2"


def endstation_has_control(
    access_control: HutchAccessControl, expected_hutch: HutchState
) -> Callable[[], Awaitable[bool]]:
    async def inner() -> bool:
        active_hutch = await access_control.active_hutch.get_value()
        return active_hutch == expected_hutch

    return inner
