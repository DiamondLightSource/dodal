from typing import TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StrictEnum,
)
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.epics.core import (
    epics_signal_rw,
)
from ophyd_async.epics.motor import Motor

T = TypeVar("T", bound=StrictEnum)


class Positioner(StandardReadable, Movable[T]):
    """1D stage with a enum table to select positions."""

    def __init__(
        self,
        prefix: str,
        positioner_enum: type[StrictEnum],
        positioner_pv_suffix: str = ":MP:SELECT",
        name: str = "",
    ) -> None:
        self._stage_motion = Motor(prefix=prefix)
        with self.add_children_as_readables(Format.CONFIG_SIGNAL):
            self.stage_position = epics_signal_rw(
                positioner_enum,
                read_pv=prefix + positioner_pv_suffix,
            )
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: T) -> None:
        await self.stage_position.set(value=value)


def create_positioner(
    datatype: type[T],
    prefix,
    positioner_pv_suffix: str = ":MP:SELECT",
    name: str = "",
) -> Positioner[T]:
    return Positioner[datatype](prefix, datatype, positioner_pv_suffix, name)
