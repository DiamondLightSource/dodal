from enum import StrEnum

from bluesky.protocols import Movable, Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_x

from dodal.devices.i19.mapt_configuration import MAPTConfiguration
from dodal.devices.motors import XYStage
from dodal.log import LOGGER

_PIN = "-MO-PIN-01:"
_COL = "-MO-COL-01:"
_CONFIG = "-OP-PCOL-01:"


APERTURE_SIZES = [20, 40, 100, 3000]


class ApertureDemand(StrEnum):
    PCOL20 = "20um"
    PCOL40 = "40um"
    PCOL100 = "100um"
    PCOL3000 = "3000um"
    OUT = "OUT"


class PinColConfigChoices(StrictEnum):
    PCOL20 = "20um"
    PCOL40 = "40um"
    PCOL100 = "100um"
    PCOL3000 = "3000um"
    PINOUT = "OUT - PINX"
    COLOUT = "OUT - COLX"


class PinholeStage(XYStage, Movable):
    """Pinhole stages xy motors."""

    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, name)

    @AsyncStatus.wrap
    async def set(self, value: dict[str, float]):
        LOGGER.debug(f"Move pinhole stage to {value}")
        await self.x.set(value["pinx"])
        if value["piny"]:
            # Account for "out" which only moves x
            await self.y.set(value["piny"])


class CollimatorStage(XYStage, Movable):
    """Collimator stage xy motors."""

    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, name)

    @AsyncStatus.wrap
    async def set(self, value: dict[str, float]):
        LOGGER.debug(f"Move collimator stage to {value}")
        await self.x.set(value["colx"])
        if value["coly"]:
            # Account for "out" which only moves x
            await self.y.set(value["coly"])


class PinColConfiguration(StandardReadable):
    def __init__(
        self, prefix: str, apertures: list[int] = APERTURE_SIZES, name: str = ""
    ) -> None:
        with self.add_children_as_readables():
            self.selection = epics_signal_rw(PinColConfigChoices, f"{prefix}")
            self.apply_selection = epics_signal_x(int, f"{prefix}:APPLY.PROC")
            self.pin_x = MAPTConfiguration(prefix, "PINX", apertures)
            self.pin_y = MAPTConfiguration(prefix, "PINY", apertures)
            self.col_x = MAPTConfiguration(prefix, "COLX", apertures)
            self.col_y = MAPTConfiguration(prefix, "COLY", apertures)
            self.pin_x_out = epics_signal_r(float, f"{prefix}:OUT:PINX")
            self.col_x_out = epics_signal_r(float, f"{prefix}:OUT:COLX")
        super().__init__(name)


class PinColControl(StandardReadable, Triggerable):
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
        super().__init__(name=name)

    def _get_aperture_size(self, request: str) -> int:
        return int(request.strip("um"))

    async def get_pinhole_motor_positions_for_requested_aperture(
        self, request: ApertureDemand
    ) -> dict[str, float]:
        # NOTE I think instead f this I should be able to do a reading ? To be checked
        val = self._get_aperture_size(request.value)

        pinx = await self.config.pin_x.in_positions[val].get_value()
        piny = await self.config.pin_y.in_positions[val].get_value()

        positions = {"pinx": pinx, "piny": piny}
        return positions

    async def get_collimator_motor_positions_for_requested_aperture(
        self, request: ApertureDemand
    ) -> dict[str, float]:
        val = self._get_aperture_size(request.value)

        colx = await self.config.col_x.in_positions[val].get_value()
        coly = await self.config.col_x.in_positions[val].get_value()

        positions = {"colx": colx, "coly": coly}
        return positions
