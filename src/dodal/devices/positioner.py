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


class Positioner(StandardReadable, Movable):
    """1D stage with a enum table to select positions."""

    def __init__(
        self,
        prefix: str,
        positioner_enum: type[StrictEnum],
        positioner_suffix: str = "",
        Positioner_pv_suffix: str = ":MP:SELECT",
        name: str = "",
    ) -> None:
        self._stage_motion = Motor(prefix=prefix + positioner_suffix)
        with self.add_children_as_readables(Format.CONFIG_SIGNAL):
            self.stage_position = epics_signal_rw(
                positioner_enum,
                read_pv=prefix + positioner_suffix + Positioner_pv_suffix,
            )
        super().__init__(name=name)
        self.positioner_enum = positioner_enum

    @AsyncStatus.wrap
    async def set(self, value: StrictEnum) -> None:
        if value in self.positioner_enum:
            await self.stage_position.set(value=value)
        else:
            raise TypeError(
                f"{value} is not an allow position. Position must be: {self.positioner_enum}"
            )
