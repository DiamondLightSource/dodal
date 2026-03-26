from abc import abstractmethod

from ophyd_async.core import StrictEnum, derived_signal_rw
from ophyd_async.epics.motor import Motor


class TemperatureControllerPosition(StrictEnum):
    SAFE = "Safe"
    BEAM = "Beam"


class TemperatureController(Motor):
    def __init__(self, prefix: str):
        self.position = derived_signal_rw(
            self._get_position,
            self._set_position,
            current_position=self,
        )
        super().__init__(prefix)

    @property
    @abstractmethod
    def _safe_position(self) -> float: ...

    @property
    @abstractmethod
    def _beam_position(self) -> float: ...

    def _get_position(self, current_position) -> TemperatureControllerPosition:
        if current_position == self._safe_position:
            return TemperatureControllerPosition.SAFE
        elif current_position == self._beam_position:
            return TemperatureControllerPosition.BEAM
        raise ValueError(
            f"Device's position {current_position} is not {TemperatureControllerPosition.SAFE}: "
            f"{self._safe_position} or {TemperatureControllerPosition.BEAM}: {self._beam_position}"
        )

    async def _set_position(self, position: TemperatureControllerPosition):
        if position == TemperatureControllerPosition.SAFE:
            await self.set(self._safe_position)
        elif position == TemperatureControllerPosition.BEAM:
            await self.set(self._beam_position)
