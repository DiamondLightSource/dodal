from typing import TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    EnumTypes,
    StandardReadable,
)
from ophyd_async.epics.core import epics_signal_rw

StrictEnumT = TypeVar("StrictEnumT", bound=EnumTypes)


class GenericFastShutter(StandardReadable, Movable[StrictEnumT]):
    """
    Basic enum device specialised for a fast shutter with configured open_state and
    close_state so it is generic enough to be used with any device or plan without
    knowing the specific enum to use.

    For example:
        await shutter.set(shutter.open_state)
        await shutter.set(shutter.close_state)
    OR
        RE(bps.mv(shutter, shutter.open_state))
        RE(bps.mv(shutter, shutter.close_state))
    """

    def __init__(
        self,
        prefix: str,
        open_state: StrictEnumT,
        close_state: StrictEnumT,
        name: str = "",
    ):
        """
        Arguments:
            prefix: The prefix for the shutter device.
            open_state: The enum value that corresponds with opening the shutter.
            close_state: The enum value that corresponds with closing the shutter.
        """
        self.open_state = open_state
        self.close_state = close_state
        with self.add_children_as_readables():
            self.state = epics_signal_rw(type(self.open_state), prefix)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: StrictEnumT) -> None:
        await self.state.set(value)

    async def is_open(self) -> bool:
        """Checks to see if shutter is currently open"""
        return await self.state.get_value() == self.open_state

    async def is_closed(self) -> bool:
        """Checks to see if shutter is currently closed"""
        return await self.state.get_value() == self.close_state
