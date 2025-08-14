from typing import Generic, TypeVar

from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.eurotherm import EurothermAutotune, EurothermGeneral

EU = TypeVar("EU", bound=EurothermGeneral)


class CyberstarBlowerEnable(StrictEnum):
    ENABLE = "Enabled"
    DISABLE = "Disabled"


class CyberstarBlower(StandardReadable, Generic[EU]):
    """This is a specific device that uses a Eurotherm controller"""

    def __init__(
        self,
        prefix: str,
        name: str = "",
        controller_type: type[EU] = EurothermGeneral,
    ):
        self.enable = epics_signal_rw(CyberstarBlowerEnable, f"{prefix}DISABLE")
        self.controller = controller_type(prefix, name)

        super().__init__(name=name)


class AutotunedCyberstarBlower(CyberstarBlower[EurothermGeneral]):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        controller_type: type[EU] = EurothermGeneral,
    ):
        self.autotune = EurothermAutotune(prefix)
        super().__init__(prefix, name=name, controller_type=controller_type)
