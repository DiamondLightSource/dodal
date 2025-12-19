from typing import Generic, Protocol, TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    EnumTypes,
    Reference,
    SignalRW,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_rw,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.selectable_source import SelectedSource, get_obj_from_selected_source

EnumTypesT = TypeVar("EnumTypesT", bound=EnumTypes)


class FastShutter(Movable[EnumTypesT], Protocol, Generic[EnumTypesT]):
    """
    Enum device specialised for a fast shutter with configured open_state and
    close_state so it is generic enough to be used with any device or plan without
    knowing the specific enum to use.

    For example:
        await shutter.set(shutter.open_state)
        await shutter.set(shutter.close_state)
    OR
        run_engine(bps.mv(shutter, shutter.open_state))
        run_engine(bps.mv(shutter, shutter.close_state))
    """

    open_state: EnumTypesT
    close_state: EnumTypesT
    shutter_state: SignalRW[EnumTypesT]

    @AsyncStatus.wrap
    async def set(self, state: EnumTypesT):
        await self.shutter_state.set(state)


class GenericFastShutter(
    StandardReadable, FastShutter[EnumTypesT], Generic[EnumTypesT]
):
    """
    Implementation of fast shutter that connects to an epics pv. This pv is an enum that
    controls the open and close state of the shutter.
    """

    def __init__(
        self,
        pv: str,
        open_state: EnumTypesT,
        close_state: EnumTypesT,
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
            self.shutter_state = epics_signal_rw(type(self.open_state), pv)
        super().__init__(name)


class DualFastShutter(StandardReadable, FastShutter[EnumTypesT], Generic[EnumTypesT]):
    """
    A fast shutter device that handles the positions of two other fast shutters. The
    "active" shutter is the one that corrosponds to the selected_shutter signal. For
    example, active shutter is shutter1 if selected_source is at SelectedSource.SOURCE1
    and vise versa for shutter2 and SelectedSource.SOURCE2. Whenever a move is done on
    this device, the inactive shutter is always set to the close_state.
    """

    def __init__(
        self,
        shutter1: GenericFastShutter[EnumTypesT],
        shutter2: GenericFastShutter[EnumTypesT],
        selected_source: SignalRW[SelectedSource],
        name: str = "",
    ):
        """
        Arguments:
            shutter1: Active shutter that corrosponds to SelectedSource.SOURCE1.
            shutter2: Active shutter that corrosponds to SelectedSource.SOURCE2.
            selected_source: Signal that decides the active shutter.
            name: Name of this device.
        """
        self._validate_shutter_states(shutter1.open_state, shutter2.open_state)
        self._validate_shutter_states(shutter1.close_state, shutter2.close_state)
        self.open_state = shutter1.open_state
        self.close_state = shutter1.close_state

        self._shutter1_ref = Reference(shutter1)
        self._shutter2_ref = Reference(shutter2)
        self._selected_shutter_ref = Reference(selected_source)

        with self.add_children_as_readables():
            self.shutter_state = derived_signal_rw(
                self._read_shutter_state,
                self._set_shutter_state,
                selected_shutter=selected_source,
                shutter1=shutter1.shutter_state,
                shutter2=shutter2.shutter_state,
            )

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.shutter1_device_name, _ = soft_signal_r_and_setter(
                str, initial_value=shutter1.name
            )
            self.shutter2_device_name, _ = soft_signal_r_and_setter(
                str, initial_value=shutter2.name
            )

        self.add_readables([shutter1, shutter2, selected_source])

        super().__init__(name)

    def _validate_shutter_states(self, state1: EnumTypesT, state2: EnumTypesT) -> None:
        if state1 is not state2:
            raise ValueError(
                f"{state1} is not same value as {state2}. They must be the same to be compatible."
            )

    def _read_shutter_state(
        self,
        selected_shutter: SelectedSource,
        shutter1: EnumTypesT,
        shutter2: EnumTypesT,
    ) -> EnumTypesT:
        return get_obj_from_selected_source(selected_shutter, shutter1, shutter2)

    async def _set_shutter_state(self, value: EnumTypesT):
        selected_shutter = await self._selected_shutter_ref().get_value()
        active_shutter = get_obj_from_selected_source(
            selected_shutter,
            self._shutter1_ref(),
            self._shutter2_ref(),
        )
        inactive_shutter = get_obj_from_selected_source(
            selected_shutter,
            self._shutter2_ref(),
            self._shutter1_ref(),
        )
        await inactive_shutter.set(inactive_shutter.close_state)
        await active_shutter.set(value)
