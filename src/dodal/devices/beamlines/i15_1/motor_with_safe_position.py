from abc import abstractmethod

from ophyd_async.core import derived_signal_rw
from ophyd_async.epics.motor import Motor

XPDF_PARAMETERS_FILEPATH = "/dls_sw/i15-1/software/gda_var/xpdfLocalParameters.xml"


class MotorWithSafePosition(Motor):
    def __init__(self, prefix: str):
        self.in_safe_position = derived_signal_rw(
            self._is_in_safe_position,
            self._set_to_safe_position,
            current_position=self,
        )
        super().__init__(prefix)

    @property
    @abstractmethod
    def _safe_position(self) -> float: ...

    def _is_in_safe_position(self, current_position) -> bool:
        return current_position == self._safe_position

    async def _set_to_safe_position(self, value: bool = True):
        if not value:
            raise ValueError("Cannot set blower to 'not safe' this way.")
        await self.set(self._safe_position)
