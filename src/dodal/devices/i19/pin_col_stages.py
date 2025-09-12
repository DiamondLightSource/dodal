# import asyncio

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable, SubsetEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_x

from dodal.devices.i19.mapt_configuration import MAPTConfiguration
from dodal.devices.motors import XYStage
from dodal.log import LOGGER

_PIN = "-MO-PIN-01:"
_COL = "-MO-COL-01:"
_CONFIG = "-OP-PCOL-01:"


class PinColRequest(SubsetEnum):
    # NOTE. Using subset anum because from the OUT positions should only be used by
    # the beamline scientists from the synoptic.
    # Will need another option for OUT position
    PCOL20 = "20um"
    PCOL40 = "40um"
    PCOL100 = "100um"
    PCOL3000 = "3000um"


def define_allowed_aperture_requests() -> list[str]:
    aperture_list = [v.value for v in PinColRequest]
    aperture_list.append("OUT")
    return aperture_list


class PinColConfiguration(StandardReadable):
    def __init__(self, prefix: str, apertures: list[int], name: str = "") -> None:
        with self.add_children_as_readables():
            self.selection = epics_signal_rw(PinColRequest, f"{prefix}")
            self.pin_x = MAPTConfiguration(prefix, "PINX", apertures)
            self.pin_y = MAPTConfiguration(prefix, "PINY", apertures)
            self.col_x = MAPTConfiguration(prefix, "COLX", apertures)
            self.col_y = MAPTConfiguration(prefix, "COLY", apertures)
            self.pin_x_out = epics_signal_r(float, f"{prefix}:OUT:PINX")
            self.col_x_out = epics_signal_r(float, f"{prefix}:OUT:COLX")
        self.apply_selection = epics_signal_x(f"{prefix}:APPLY.PROC")
        super().__init__(name)


class PinColControl(StandardReadable, Movable[str]):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        pin_infix: str = _PIN,
        col_infix: str = _COL,
        config_infix: str = _CONFIG,
    ):
        self._allowed_requests = define_allowed_aperture_requests()
        self._aperture_sizes = [self._get_aperture_size(i) for i in PinColRequest]
        with self.add_children_as_readables():
            self.pinhole = XYStage(f"{prefix}{pin_infix}")
            self.collimator = XYStage(f"{prefix}{col_infix}")
            self.config = PinColConfiguration(
                f"{prefix}{config_infix}CONFIG", apertures=self._aperture_sizes
            )
        super().__init__(name=name)

    def _get_aperture_size(self, request: str) -> int:
        return int(request.strip("um"))

    async def get_pinhole_motor_positions_for_requested_aperture(
        self, request: PinColRequest
    ) -> dict[str, float]:
        val = self._get_aperture_size(request.value)

        pinx = await self.config.pin_x.in_positions[val].get_value()
        piny = await self.config.pin_y.in_positions[val].get_value()

        positions = {"pinx": pinx, "piny": piny}
        return positions

    async def get_collimator_motor_positions_for_requested_aperture(
        self, request: PinColRequest
    ) -> dict[str, float]:
        val = self._get_aperture_size(request.value)

        colx = await self.config.col_x.in_positions[val].get_value()
        coly = await self.config.col_x.in_positions[val].get_value()

        positions = {"colx": colx, "coly": coly}
        return positions

    async def _safe_move_out(self):
        colx_out = await self.config.col_x_out.get_value()
        pin_x_out = await self.config.pin_x_out.get_value()
        # First move Collimator x motor
        LOGGER.debug(f"Move collimator stage x motor to {colx_out}")
        await self.collimator.x.set(colx_out)
        # Then move Pinhole x motor
        LOGGER.debug(f"Move pinhole stage x motor to {pin_x_out}")
        await self.pinhole.x.set(pin_x_out)

    async def _safe_move_in(self, value: PinColRequest):
        # The moves should be done in a safe way by apply button in controls
        # TODO double check that collisions are actually avoided
        # First move Pinhole motors, then move Collimator motors
        await self.config.selection.set(value)
        await self.config.apply_selection.trigger()
        # Check motors have stopped moving here

    @AsyncStatus.wrap
    async def set(self, value: str):
        # The request from a plan would always oly be either one of the
        # 4 allowed apertures values in PinColRequest or "OUT" which always moves
        # first colx out and then pinx
        # This is to avoid collisions.
        if value not in self._allowed_requests:
            raise ValueError(
                f"""{value} is not a valid aperture request.
                Please pass one of: {self._allowed_requests}."""
            )
        if value == "OUT":
            LOGGER.info("Moving pinhole and collimator stages to out position")
            await self._safe_move_out()
        else:
            await self._safe_move_in(PinColRequest(value))
