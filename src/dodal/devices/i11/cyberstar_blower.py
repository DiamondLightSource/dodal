from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.eurotherm import EurothermAutotune, EurothermGeneral, EurothermPID


class CyberstarBlower(EurothermGeneral):
    def __init__(
        self,
        prefix: str,
        name="",
        enable_suffix: str = "DISABLE",
        infix: str = "",
        update=False,
        autotune=False,
    ):
        self.enable = epics_signal_rw(str, f"{prefix}{enable_suffix}")
        self.tune = EurothermPID(prefix=prefix + infix, update=update)

        if autotune:
            self.autotune = EurothermAutotune(prefix=prefix + infix)

        super().__init__(prefix=prefix + infix, name=name, update=update)
