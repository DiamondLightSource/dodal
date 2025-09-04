from bluesky.protocols import Movable
from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_rw

from dodal.devices.motors import XYStage

_PIN = "-MO-PIN-01:"
_COL = "-MO-COL-01:"
_CONFIG = "-OP-PCOL-01:"


class PinholeStage(XYStage):
    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, name)


class CollimatorStage(XYStage):
    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, name)


class PinColControl(StandardReadable, Movable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        pin_infix: str = _PIN,
        col_infix: str = _COL,
        config_infix: str = _CONFIG,
    ):
        with self.add_children_as_readables():
            self.pinhole = PinholeStage(f"{prefix}{pin_infix}")
            self.collimator = CollimatorStage(f"{prefix}{col_infix}")
            self.config = epics_signal_rw(int, f"{prefix}{config_infix}CONFIG")
        super().__init__(name=name)
