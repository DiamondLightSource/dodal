from typing import Generic

from ophyd_async.core import AsyncStatus, StrictEnum

from dodal.devices.enum_device import EnumDevice, StrictEnumT


class GenericShutter(EnumDevice[StrictEnumT], Generic[StrictEnumT]):
    """
    Shutter with configured open and close states so it can be used with any device or
    plan, no matter what the underlying PV enum takes.
    """

    def __init__(
        self,
        prefix: str,
        enum_type: type[StrictEnumT],
        open: StrictEnum,
        close: StrictEnum,
    ):
        """
        Arguments:
            prefix: the prefix for the shutter device.
            enum_type: The enum that the shutter takes.
            open: The enum that corrosponds with opening the shutter.
            close: The enum that corrosponds with closing the shutter.
        """
        self.open = open
        self.close = close
        super().__init__(prefix, enum_type)

    @AsyncStatus.wrap
    async def set(self, value: StrictEnumT) -> None:
        """
        Move the shutter to an open or close state. Raise error if attempted to a
        different position. Can be used generically inside plans or devices by moving
        like this example:
            await shutter.set(shutter.open)
            await shutter.set(shutter.close)
        """
        if value is not self.open and value is not self.close:
            raise ValueError()
        await super().set(value)

    async def is_open(self) -> bool:
        """Checks to see if shutter is currently open"""
        return await self.state.get_value() == self.open

    async def is_closed(self) -> bool:
        """Checks to see if shutter is currently closed"""
        return await self.state.get_value() == self.close
