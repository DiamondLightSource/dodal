from typing import Generic, TypeVar

from ophyd_async.core import EnabledDisabled, StandardReadable
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.eurotherm import EurothermAutotune, EurothermGeneral

EU = TypeVar("EU", bound=EurothermGeneral)


class CyberstarBlower(StandardReadable, Generic[EU]):
    """This is a specific device that uses a Eurotherm controller"""

    def __init__(
        self,
        prefix: str,
        name: str = "",
        controller_type: type[EU] = EurothermGeneral,
    ):
        self.enable = epics_signal_rw(EnabledDisabled, f"{prefix}DISABLE")
        self.controller = controller_type(prefix, name)

        super().__init__(name=name)


class AutotunedCyberstarBlower(Generic[EU], CyberstarBlower[EU]):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        controller_type: type[EU] = EurothermGeneral,
    ):
        self.autotune = EurothermAutotune(prefix)
        super().__init__(prefix, name=name, controller_type=controller_type)
