import asyncio

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable, SubsetEnum
from ophyd_async.epics.core import epics_signal_r
from pydantic import BaseModel

from dodal.devices.i19.mapt_configuration import (
    MAPTConfigurationControl,
    MAPTConfigurationTable,
)
from dodal.devices.motors import XYStage
from dodal.log import LOGGER

_PIN = "-MO-PIN-01:"
_COL = "-MO-COL-01:"
_CONFIG = "-OP-PCOL-01:"


# NOTE. Using subset anum because from the OUT positions should only be used by
# the beamline scientists from the synoptic. Another option will be needed in the
# device for OUT position.
class PinColRequest(SubsetEnum):
    """Aperture request IN positions."""

    PCOL20 = "20um"
    PCOL40 = "40um"
    PCOL100 = "100um"
    PCOL3000 = "3000um"


class AperturePosition(BaseModel):
    """Describe the positions of the pinhole and collimator stage motors for
    one of the available apertures.

    Attributes:
        pinhole_x: The position of the x motor on the pinhole stage
        pinhole_y: The position of the y motor on the pinhole stage
        collimator_x: The position of the x motor on the collimator stage
        collimator_y: The position of the y motor on the collimator stage
    """

    pinhole_x: float
    pinhole_y: float
    collimator_x: float
    collimator_y: float


def define_allowed_aperture_requests() -> list[str]:
    aperture_list = [v.value for v in PinColRequest]
    aperture_list.append("OUT")
    return aperture_list


class PinColConfiguration(StandardReadable):
    """Full MAPT configuration table, including out positions and selection for the
    Pinhole and Collimator control."""

    def __init__(self, prefix: str, apertures: list[int], name: str = "") -> None:
        with self.add_children_as_readables():
            self.configuration = MAPTConfigurationControl(prefix, PinColRequest)
            self.pin_x = MAPTConfigurationTable(prefix, "PINX", apertures)
            self.pin_y = MAPTConfigurationTable(prefix, "PINY", apertures)
            self.col_x = MAPTConfigurationTable(prefix, "COLX", apertures)
            self.col_y = MAPTConfigurationTable(prefix, "COLY", apertures)
            self.pin_x_out = epics_signal_r(float, f"{prefix}:OUT:PINX")
            self.col_x_out = epics_signal_r(float, f"{prefix}:OUT:COLX")
        super().__init__(name)


class PinholeCollimatorControl(StandardReadable, Movable[str]):
    """Device to control the Pinhole and Collimator stages moves on I19-2, using the
    MAPT configuration table to look up the positions."""

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

    async def get_motor_positions_for_requested_aperture(
        self, request: PinColRequest
    ) -> AperturePosition:
        val = self._get_aperture_size(request.value)

        pinx = await self.config.pin_x.in_positions[val].get_value()
        piny = await self.config.pin_y.in_positions[val].get_value()
        colx = await self.config.col_x.in_positions[val].get_value()
        coly = await self.config.col_x.in_positions[val].get_value()

        return AperturePosition(
            pinhole_x=pinx, pinhole_y=piny, collimator_x=colx, collimator_y=coly
        )

    async def _safe_move_out(self):
        """Move the pinhole and collimator stages safely to the out position, which
        involves only the x motors of the stages.
        In order to avoid a collision, we have to make sure that the collimator stage is
        always moved out first and the pinhole stage second.
        """
        LOGGER.info("Moving pinhole and collimator stages to out position")
        colx_out = await self.config.col_x_out.get_value()
        pin_x_out = await self.config.pin_x_out.get_value()
        # First move Collimator x motor
        LOGGER.debug(f"Move collimator stage x motor to {colx_out}")
        await self.collimator.x.set(colx_out)
        # Then move Pinhole x motor
        LOGGER.debug(f"Move pinhole stage x motor to {pin_x_out}")
        await self.pinhole.x.set(pin_x_out)

    async def _safe_move_in(self, value: PinColRequest):
        """Move the pinhole and collimator stages safely to the in position.
        In order to avoid a collision, we have to make sure that the pinhole stage is
        always moved in before the collimator stage."""
        LOGGER.info(
            f"Moving pinhole and collimator stages to in position: {value.value}"
        )
        await self.config.configuration.select_config.set(value)
        # NOTE. The apply PV will not be used here unless fixed in controls first.
        # This is to avoid collisions. A safe move in will move first the pinhole stage
        # and then the collimator stage, but apply will try to move all the motors
        # at the same time.
        aperture_positions = await self.get_motor_positions_for_requested_aperture(
            value
        )
        LOGGER.debug(f"Moving motors to {aperture_positions}")

        # First move Pinhole motors,
        LOGGER.debug("Move pinhole stage in")
        await asyncio.gather(
            self.pinhole.x.set(aperture_positions.pinhole_x),
            self.pinhole.y.set(aperture_positions.pinhole_y),
        )
        # Then move Collimator motors
        LOGGER.debug("Move pinhole stage in")
        await asyncio.gather(
            self.collimator.x.set(aperture_positions.collimator_x),
            self.collimator.y.set(aperture_positions.collimator_y),
        )

    @AsyncStatus.wrap
    async def set(self, value: str):
        """Moves the motor stages to the position for the requested aperture while
        avoiding possible collisions.
        The request coming from a plan should always be one of the values from the
        PinColRequest enum ('20um', '40um', '100um', '3000um') or "OUT".

        Raises:
            ValueError: when the request doesn't match one of the allowed requests:
                ['20um', '40um', '100um', '3000um', 'OUT']
        """
        if value not in self._allowed_requests:
            raise ValueError(
                f"""{value} is not a valid aperture request.
                Please pass one of: {self._allowed_requests}."""
            )
        if value == "OUT":
            await self._safe_move_out()
        else:
            await self._safe_move_in(PinColRequest(value))
