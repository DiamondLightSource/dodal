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
        run_engine(bps.mv(shutter, shutter.open_state))
        run_engine(bps.mv(shutter, shutter.close_state))
    """

    def __init__(
        self,
        pv: str,
        open_state: StrictEnumT,
        close_state: StrictEnumT,
        name: str = "",
    ):
        """
        Arguments:
            pv: The pv to connect to the shutter device.
            open_state: The enum value that corresponds with opening the shutter.
            close_state: The enum value that corresponds with closing the shutter.
        """
        self.open_state = open_state
        self.close_state = close_state
        with self.add_children_as_readables():
            self.state = epics_signal_rw(type(self.open_state), pv)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: StrictEnumT) -> None:
        await self.state.set(value)

    async def is_open(self) -> bool:
        """
        Checks to see if shutter is in open_state. Should not be used directly inside a
        plan. A user should use the following instead in a plan:

            from bluesky import plan_stubs as bps
            is_open = yield from bps.rd(shutter.state) == shutter.open_state
        """
        return await self.state.get_value() == self.open_state

    async def is_closed(self) -> bool:
        """
        Checks to see if shutter is in close_state. Should not be used directly inside a
        plan. A user should use the following instead in a plan:

            from bluesky import plan_stubs as bps
            is_closed = yield from bps.rd(shutter.state) == shutter.close_state
        """
        return await self.state.get_value() == self.close_state
