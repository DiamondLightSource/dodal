from abc import abstractmethod
from typing import TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    EnumTypes,
    Reference,
    StandardReadable,
    StrictEnum,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_rw

StrictEnumT = TypeVar("StrictEnumT", bound=EnumTypes)


class AbstractFastShutter(StandardReadable, Movable[StrictEnumT]):
    def __init__(self, open_state: StrictEnumT, close_state: StrictEnumT, name: str):
        self.open_state = open_state
        self.close_state = close_state
        super().__init__(name)

    @abstractmethod
    @AsyncStatus.wrap
    async def set(self, state: StrictEnumT) -> None:
        """"""


class GenericFastShutter(AbstractFastShutter[StrictEnumT]):
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
        with self.add_children_as_readables():
            self.state = epics_signal_rw(type(self.open_state), pv)
        super().__init__(open_state, close_state, name)

    @AsyncStatus.wrap
    async def set(self, state: StrictEnumT) -> None:
        await self.state.set(state)


class SelectedDevice(StrictEnum):
    DEVICE1 = "device1"
    DEVICE2 = "device2"


T = TypeVar("T")


def get_obj_from_selected_device(
    selected_device: SelectedDevice, selected_source1_obj: T, selected_source2_obj: T
) -> T:
    match selected_device:
        case SelectedDevice.DEVICE1:
            return selected_source1_obj
        case SelectedDevice.DEVICE2:
            return selected_source2_obj


class DualFastShutter(AbstractFastShutter[StrictEnumT]):
    def __init__(
        self, shutter1: GenericFastShutter, shutter2: GenericFastShutter, name: str
    ):
        if shutter1.open_state is not shutter2.open_state:
            raise Exception("")
        if shutter1.close_state is not shutter2.close_state:
            raise Exception("")

        open_state = shutter1.open_state
        close_state = shutter1.close_state

        self.shutter1_ref = Reference(shutter1)
        self.shutter2_ref = Reference(shutter2)

        self.selected_shutter = soft_signal_rw(
            SelectedDevice, initial_value=SelectedDevice.DEVICE1
        )
        super().__init__(open_state, close_state, name)

    async def get_active_shutter(self) -> GenericFastShutter:
        return get_obj_from_selected_device(
            await self.selected_shutter.get_value(),
            selected_source1_obj=self.shutter1_ref(),
            selected_source2_obj=self.shutter2_ref(),
        )

    async def get_inactive_shutter(self) -> GenericFastShutter:
        return get_obj_from_selected_device(
            await self.selected_shutter.get_value(),
            selected_source1_obj=self.shutter2_ref(),
            selected_source2_obj=self.shutter1_ref(),
        )

    @AsyncStatus.wrap
    async def set(self, state: StrictEnumT):
        inactive_shutter = await self.get_inactive_shutter()
        await inactive_shutter.set(self.close_state)
        active_shutter = await self.get_active_shutter()
        await active_shutter.set(state)
