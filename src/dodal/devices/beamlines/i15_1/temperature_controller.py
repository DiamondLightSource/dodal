from abc import abstractmethod

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StrictEnum,
)
from ophyd_async.epics.motor import Motor


class TemperatureControllerPosition(StrictEnum):
    SAFE = "Safe"
    BEAM = "Beam"


class TemperatureController(StandardReadable, Movable[TemperatureControllerPosition]):
    def __init__(self, prefix: str):
        with self.add_children_as_readables():
            self.motor = Motor(prefix=prefix)
        super().__init__(prefix)

    @property
    @abstractmethod
    def _safe_position(self) -> float: ...

    @property
    @abstractmethod
    def _beam_position(self) -> float: ...

    @AsyncStatus.wrap
    async def set(self, value: TemperatureControllerPosition):
        if value == TemperatureControllerPosition.SAFE:
            await self.motor.set(self._safe_position)
        elif value == TemperatureControllerPosition.BEAM:
            await self.motor.set(self._beam_position)
