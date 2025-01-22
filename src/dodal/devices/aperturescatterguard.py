from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from bluesky.protocols import Movable, Triggerable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.motor import Motor
from pydantic import BaseModel, Field

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.common.signal_utils import create_hardware_backed_soft_signal
from dodal.devices.aperture import Aperture
from dodal.devices.scatterguard import Scatterguard


class InvalidApertureMove(Exception):
    pass


class AperturePosition(BaseModel):
    """
    Represents one of the available positions for the Aperture-Scatterguard.
    Attributes:
        aperture_x: The x position of the aperture component in mm
        aperture_y: The y position of the aperture component in mm
        aperture_z: The z position of the aperture component in mm
        scatterguard_x: The x position of the scatterguard component in mm
        scatterguard_y: The y position of the scatterguard component in mm
        radius: Radius of the selected aperture. When in the Robot Load position, the
            radius is defined to be 0
    """

    aperture_x: float
    aperture_y: float
    aperture_z: float
    scatterguard_x: float
    scatterguard_y: float
    radius: float = Field(json_schema_extra={"units": "µm"}, default=0.0)

    @property
    def values(self) -> tuple[float, float, float, float, float]:
        return (
            self.aperture_x,
            self.aperture_y,
            self.aperture_z,
            self.scatterguard_x,
            self.scatterguard_y,
        )

    @staticmethod
    def tolerances_from_gda_params(
        params: GDABeamlineParameters,
    ) -> AperturePosition:
        return AperturePosition(
            aperture_x=params["miniap_x_tolerance"],
            aperture_y=params["miniap_y_tolerance"],
            aperture_z=params["miniap_z_tolerance"],
            scatterguard_x=params["sg_x_tolerance"],
            scatterguard_y=params["sg_y_tolerance"],
        )

    @staticmethod
    def from_gda_params(
        name: ApertureValue,
        radius: float,
        params: GDABeamlineParameters,
    ) -> AperturePosition:
        return AperturePosition(
            aperture_x=params[f"miniap_x_{name.value}"],
            aperture_y=params[f"miniap_y_{name.value}"],
            aperture_z=params[f"miniap_z_{name.value}"],
            scatterguard_x=params[f"sg_x_{name.value}"],
            scatterguard_y=params[f"sg_y_{name.value}"],
            radius=radius,
        )


class ApertureValue(StrictEnum):
    """Maps from a short usable name to the value name in the GDA Beamline parameters"""

    ROBOT_LOAD = "ROBOT_LOAD"
    SMALL = "SMALL_APERTURE"
    MEDIUM = "MEDIUM_APERTURE"
    LARGE = "LARGE_APERTURE"

    def __str__(self):
        return self.name.capitalize()


def load_positions_from_beamline_parameters(
    params: GDABeamlineParameters,
) -> dict[ApertureValue, AperturePosition]:
    return {
        ApertureValue.ROBOT_LOAD: AperturePosition.from_gda_params(
            ApertureValue.ROBOT_LOAD, 0, params
        ),
        ApertureValue.SMALL: AperturePosition.from_gda_params(
            ApertureValue.SMALL, 20, params
        ),
        ApertureValue.MEDIUM: AperturePosition.from_gda_params(
            ApertureValue.MEDIUM, 50, params
        ),
        ApertureValue.LARGE: AperturePosition.from_gda_params(
            ApertureValue.LARGE, 100, params
        ),
    }


async def _safe_move_whilst_in_beam(
    aperture: Aperture,
    scatterguard: Scatterguard,
    position: AperturePosition,
    aperture_z_tolerance: float,
):
    """
    Move the aperture and scatterguard combo safely to a new position.
    See https://github.com/DiamondLightSource/hyperion/wiki/Aperture-Scatterguard-Collisions
    for why this is required. TLDR is that we have a collision at the top of y so we need
    to make sure we move the assembly down before we move the scatterguard up.

    We also check that the assembly has been moved into the correct z position
    previously. If we try and move whilst in the incorrect Z position we will collide
    with the table.
    """
    ap_z_in_position = await aperture.z.motor_done_move.get_value()
    if not ap_z_in_position:
        raise InvalidApertureMove(
            "ApertureScatterguard z is still moving. Wait for it to finish "
            "before triggering another move."
        )

    current_ap_z = await aperture.z.user_readback.get_value()
    diff_on_z = abs(current_ap_z - position.aperture_z)
    if diff_on_z > aperture_z_tolerance:
        raise InvalidApertureMove(
            f"Current aperture z ({current_ap_z}), outside of tolerance ({aperture_z_tolerance}) from target ({position.aperture_z})."
        )

    current_ap_y = await aperture.y.user_readback.get_value()

    aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = position.values

    if aperture_y > current_ap_y:
        # Assembly needs to move up so move the scatterguard down first
        await asyncio.gather(
            scatterguard.x.set(scatterguard_x),
            scatterguard.y.set(scatterguard_y),
        )
        await asyncio.gather(
            aperture.x.set(aperture_x),
            aperture.y.set(aperture_y),
            aperture.z.set(aperture_z),
        )
    else:
        await asyncio.gather(
            aperture.x.set(aperture_x),
            aperture.y.set(aperture_y),
            aperture.z.set(aperture_z),
        )

        await asyncio.gather(
            scatterguard.x.set(scatterguard_x),
            scatterguard.y.set(scatterguard_y),
        )


class ApertureSelector(StandardReadable, Movable):
    """Allows for moving all axes other than Y into the correct position, this means
    that we can set up the aperture while it is out of the beam then move it in later."""

    def __init__(
        self,
        aperture: Aperture,
        scatterguard: Scatterguard,
        out_of_beam: Callable[[], Coroutine[Any, Any, bool]],
        loaded_positions: dict[ApertureValue, AperturePosition],
        aperture_z_tolerance: float,
    ):
        self.aperture = Reference(aperture)
        self.scatterguard = Reference(scatterguard)
        self.loaded_positions = loaded_positions
        self.get_is_out_of_beam = out_of_beam
        self.aperture_z_tolerance = aperture_z_tolerance
        super().__init__()

    @AsyncStatus.wrap
    async def set(self, value: ApertureValue):
        """Moves the assembly to the position for the specified aperture, whilst keeping
        it out of the beam if it already is so.

        Moving the assembly whilst out of the beam has no collision risk so we can just
        move all the motors together.
        """
        if await self.get_is_out_of_beam():
            aperture_x, _, aperture_z, scatterguard_x, scatterguard_y = (
                self.loaded_positions[value].values
            )

            await asyncio.gather(
                self.aperture().x.set(aperture_x),
                self.aperture().z.set(aperture_z),
                self.scatterguard().x.set(scatterguard_x),
                self.scatterguard().y.set(scatterguard_y),
            )
        else:
            await _safe_move_whilst_in_beam(
                self.aperture(),
                self.scatterguard(),
                self.loaded_positions[value],
                self.aperture_z_tolerance,
            )


class OutTrigger(StandardReadable, Triggerable):
    """Allows for moving just the Y stage of the assembly out of the beam."""

    def __init__(
        self,
        aperture_y: Motor,
        out_y: float,
    ):
        self.aperture_y = Reference(aperture_y)
        self.out_y = out_y
        super().__init__()

    @AsyncStatus.wrap
    async def trigger(self):
        """Moves the assembly out of the beam."""
        await self.aperture_y().set(self.out_y)


class ApertureScatterguard(StandardReadable, Movable):
    """Move the aperture and scatterguard assembly in a safe way. There are two ways to
    interact with the device depending on if you want simplicity or move flexibility.

    Examples:
        The simple interface is using::

            await aperture_scatterguard.set(ApertureValue.LARGE)

        This will move the assembly so that the large aperture is in the beam, regardless
        of where the assembly currently is.

        However, the aperture Y axis is faster than the others. In some cases we may want to
        move the assembly out of the beam with this axis without moving others::

            await aperture_scatterguard.move_out.trigger()

        We may then want to keep the assembly out of the beam whilst asynchronously preparing
        the other axes for the aperture that's to follow::

            await aperture_scatterguard.aperture_outside_beam.set(ApertureValue.LARGE)

        Then, at a later time, move back into the beam::

            await aperture_scatterguard.set(ApertureValue.LARGE)

        This move will now be faster as only the y is left to move.
    """

    def __init__(
        self,
        loaded_positions: dict[ApertureValue, AperturePosition],
        tolerances: AperturePosition,
        prefix: str = "",
        name: str = "",
    ) -> None:
        self.aperture = Aperture(prefix + "-MO-MAPT-01:")
        self.scatterguard = Scatterguard(prefix + "-MO-SCAT-01:")
        self.radius = create_hardware_backed_soft_signal(
            float, self._get_current_radius, units="µm"
        )
        self._loaded_positions = loaded_positions
        self._tolerances = tolerances
        self.add_readables(
            [
                self.aperture.x.user_readback,
                self.aperture.y.user_readback,
                self.aperture.z.user_readback,
                self.scatterguard.x.user_readback,
                self.scatterguard.y.user_readback,
                self.radius,
            ],
        )

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.selected_aperture = create_hardware_backed_soft_signal(
                ApertureValue, self._get_current_aperture_position
            )

        # Setting this will select the aperture but not move it into beam
        self.aperture_outside_beam = ApertureSelector(
            self.aperture,
            self.scatterguard,
            self._is_out_of_beam,
            self._loaded_positions,
            self._tolerances.aperture_z,
        )

        # Setting this will just move the assembly out of the beam
        self.move_out = OutTrigger(
            self.aperture.y, loaded_positions[ApertureValue.ROBOT_LOAD].aperture_y
        )

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: ApertureValue):
        """This set will move the aperture into the beam or move to robot load"""
        position = self._loaded_positions[value]
        await _safe_move_whilst_in_beam(
            self.aperture, self.scatterguard, position, self._tolerances.aperture_z
        )

    @AsyncStatus.wrap
    async def _set_raw_unsafe(self, position: AperturePosition):
        """Accept the risks and move in an unsafe way. Collisions possible."""
        aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = (
            position.values
        )

        await asyncio.gather(
            self.aperture.x.set(aperture_x),
            self.aperture.y.set(aperture_y),
            self.aperture.z.set(aperture_z),
            self.scatterguard.x.set(scatterguard_x),
            self.scatterguard.y.set(scatterguard_y),
        )

    async def _is_out_of_beam(self) -> bool:
        current_ap_y = await self.aperture.y.user_readback.get_value()
        robot_load_ap_y = self._loaded_positions[ApertureValue.ROBOT_LOAD].aperture_y
        return current_ap_y <= robot_load_ap_y + self._tolerances.aperture_y

    async def _get_current_aperture_position(self) -> ApertureValue:
        """
        Returns the current aperture position using readback values
        for SMALL, MEDIUM, LARGE. ROBOT_LOAD position defined when
        mini aperture y <= ROBOT_LOAD.location.aperture_y + tolerance.
        If no position is found then raises InvalidApertureMove.
        """
        if await self.aperture.large.get_value(cached=False) == 1:
            return ApertureValue.LARGE
        elif await self.aperture.medium.get_value(cached=False) == 1:
            return ApertureValue.MEDIUM
        elif await self.aperture.small.get_value(cached=False) == 1:
            return ApertureValue.SMALL
        elif await self._is_out_of_beam():
            return ApertureValue.ROBOT_LOAD

        raise InvalidApertureMove("Current aperture/scatterguard state unrecognised")

    async def _get_current_radius(self) -> float:
        current_value = await self._get_current_aperture_position()
        return self._loaded_positions[current_value].radius
