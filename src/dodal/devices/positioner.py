from typing import TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StrictEnum,
)
from ophyd_async.epics.core import (
    epics_signal_rw,
)
from ophyd_async.epics.motor import Motor

T = TypeVar("T", bound=StrictEnum)


class Positioner1D(StandardReadable, Movable[T]):
    """1D stage with a enum table to select positions.

    Use this when writing a device with an EPICS positioner on a single axis.
    """

    def __init__(
        self,
        prefix: str,
        datatype: type[StrictEnum],
        positioner_pv_suffix: str = ":MP:SELECT",
        name: str = "",
    ) -> None:
        self._stage_motion = Motor(prefix=prefix)
        with self.add_children_as_readables():
            self.stage_position = epics_signal_rw(
                datatype,
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
) -> Positioner1D[T]:
    return Positioner1D[datatype](prefix, datatype, positioner_pv_suffix, name)
