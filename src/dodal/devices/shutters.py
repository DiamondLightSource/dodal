from typing import Generic

from ophyd_async.core import AsyncStatus

from dodal.devices.enum_device import EnumDevice, StrictEnumT


class GenericShutter(EnumDevice[StrictEnumT], Generic[StrictEnumT]):
    """
    Shutter with configured open and close states so it can be used with any device or
    plan without knowing the specific enum to use.
    """

    def __init__(
        self,
        prefix: str,
        OPEN: StrictEnumT,
        CLOSE: StrictEnumT,
        name: str = "",
    ):
        """
        Arguments:
            prefix: The prefix for the shutter device.
            OPEN: The enum value that corrosponds with opening the shutter.
            CLOSE: The enum value that corrosponds with closing the shutter.
        """
        self.OPEN = OPEN
        self.CLOSE = CLOSE
        super().__init__(prefix, type(OPEN), name)

    @AsyncStatus.wrap
    async def set(self, value: StrictEnumT) -> None:
        """
        Move the shutter to an open or close state. Raise error if move attempted to a
        different position. Can be used generically inside plans or devices by moving
        to the configured OPEN and CLOSE states without knowing the underlying enum to
        use. For example:

            await shutter.set(shutter.OPEN)
            await shutter.set(shutter.CLOSE)

        Parameters:
            value: The open or close state.
        """
        if value is not self.OPEN and value is not self.CLOSE:
            raise ValueError(
                f"Valid states to move shutter to are {self.OPEN} and {self.CLOSE}. "
                "Requested state was {value}."
            )
        await super().set(value)

    async def is_open(self) -> bool:
        """Checks to see if shutter is currently open"""
        return await self.state.get_value() == self.OPEN

    async def is_closed(self) -> bool:
        """Checks to see if shutter is currently closed"""
        return await self.state.get_value() == self.CLOSE
