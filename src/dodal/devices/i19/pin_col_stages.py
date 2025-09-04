from bluesky.protocols import Movable
from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

from dodal.devices.i19.mapt_configuration import MAPTConfiguration
from dodal.devices.motors import XYStage

_PIN = "-MO-PIN-01:"
_COL = "-MO-COL-01:"
_CONFIG = "-OP-PCOL-01:"


APERTURE_SIZES = [20, 40, 100, 3000]


class PinColConfig(StrictEnum):
    PCOL20 = "20um"
    PCOL40 = "40um"
    PCOL100 = "100um"
    PCOL3000 = "3000um"
    PINOUT = "OUT - PINX"
    COLOUT = "OUT - COLX"


class PinColOut(StrictEnum):
    NOTOUT = "NOT OUT"
    OUT = "OUT"


class PinholeStage(XYStage):
    """Pinhole stages xy motors."""

    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, name)


class CollimatorStage(XYStage):
    """Collimator stage xy motors."""

    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, name)


class PinColConfiguration(StandardReadable):
    def __init__(
        self, prefix: str, apertures: list[int] = APERTURE_SIZES, name: str = ""
    ) -> None:
        with self.add_children_as_readables():
            self.selection = epics_signal_rw(PinColConfig, f"{prefix}CONFIG")
            self.pin_x = MAPTConfiguration(prefix, "PINX", apertures)
            self.pin_Y = MAPTConfiguration(prefix, "PINY", apertures)
            self.col_x = MAPTConfiguration(prefix, "COLX", apertures)
            self.col_y = MAPTConfiguration(prefix, "COLY", apertures)
            self.pin_x_out = epics_signal_r(float, f"{prefix}OUT:PINX")
            self.col_x_out = epics_signal_r(float, f"{prefix}OUT:COLX")
        super().__init__(name)


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
            self.config = PinColConfiguration(f"{prefix}{config_infix}CONFIG")
            self.config = epics_signal_rw(PinColConfig, f"{prefix}{config_infix}CONFIG")
            self.is_out = epics_signal_r(PinColOut, f"{prefix}{config_infix}IS_OUT")
        super().__init__(name=name)
