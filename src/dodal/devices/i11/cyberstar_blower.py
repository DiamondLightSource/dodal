from ophyd_async.core import StrictEnum
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.eurotherm import EurothermAutotune, EurothermGeneral, EurothermPID


class CyberstarBlowerEnable(StrictEnum):
    ON = "Enabled"
    OFF = "Disabled"


class CyberstarBlower(EurothermGeneral):
    """This is a specific device that uses a Eurotherm controller"""

    def __init__(
        self,
        prefix: str,
        name="",
        enable_suffix: str = "DISABLE",
        infix: str = "",
        update=False,
        autotune=False,
    ):
        with self.add_children_as_readables():
            self.enable = epics_signal_rw(
                CyberstarBlowerEnable, f"{prefix}{enable_suffix}"
            )
            self.tune = EurothermPID(prefix=prefix + infix, update=update)

            if autotune:
                self.autotune = EurothermAutotune(prefix=prefix + infix)
            else:
                self.autotune = None

        super().__init__(prefix=prefix + infix, name=name, update=update)
