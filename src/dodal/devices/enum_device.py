from typing import TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    EnumTypes,
    StandardReadable,
)
from ophyd_async.epics.core import epics_signal_rw

StrictEnumT = TypeVar("StrictEnumT", bound=EnumTypes)


class EnumDevice(StandardReadable, Movable[StrictEnumT]):
    """Simple device to hold enum state of a PV."""

    def __init__(
        self, prefix: str, enum_type: type[StrictEnumT], name: str = ""
    ) -> None:
        """
        Arguments:
            prefix: PV string to connect to device.
            enum_type: The enum that the pv takes for the device.
            name: Name of the device.
        """
        self.enum_type = enum_type
        with self.add_children_as_readables():
            self.state = epics_signal_rw(self.enum_type, prefix)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: StrictEnumT) -> None:
        await self.state.set(value)
