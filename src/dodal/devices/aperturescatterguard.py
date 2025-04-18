from __future__ import annotations

import asyncio

from bluesky.protocols import Preparable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_r,
    derived_signal_rw,
)
from pydantic import BaseModel, Field

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.aperture import Aperture
from dodal.devices.scatterguard import Scatterguard


class InvalidApertureMove(Exception):
    pass


class _GDAParamApertureValue(StrictEnum):
    """Maps from a short usable name to the value name in the GDA Beamline parameters"""

    ROBOT_LOAD = "ROBOT_LOAD"
    SMALL = "SMALL_APERTURE"
    MEDIUM = "MEDIUM_APERTURE"
    LARGE = "LARGE_APERTURE"


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
        name: _GDAParamApertureValue,
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
    """The possible apertures that can be selected.

    Changing these means changing the external paramter model of Hyperion.
    See https://github.com/DiamondLightSource/mx-bluesky/issues/760
    """

    SMALL = "SMALL_APERTURE"
    MEDIUM = "MEDIUM_APERTURE"
    LARGE = "LARGE_APERTURE"
    OUT_OF_BEAM = "Out of beam"

    def __str__(self):
        return self.name.capitalize()


def load_positions_from_beamline_parameters(
    params: GDABeamlineParameters,
) -> dict[ApertureValue, AperturePosition]:
    return {
        ApertureValue.OUT_OF_BEAM: AperturePosition.from_gda_params(
            _GDAParamApertureValue.ROBOT_LOAD, 0, params
        ),
        ApertureValue.SMALL: AperturePosition.from_gda_params(
            _GDAParamApertureValue.SMALL, 20, params
        ),
        ApertureValue.MEDIUM: AperturePosition.from_gda_params(
            _GDAParamApertureValue.MEDIUM, 50, params
        ),
        ApertureValue.LARGE: AperturePosition.from_gda_params(
            _GDAParamApertureValue.LARGE, 100, params
        ),
    }


class ApertureScatterguard(StandardReadable, Preparable):
    """Move the aperture and scatterguard assembly in a safe way. There are two ways to
    interact with the device depending on if you want simplicity or move flexibility.

    Examples:
        The simple interface is using::

            await aperture_scatterguard.selected_aperture.set(ApertureValue.LARGE)

        This will move the assembly so that the large aperture is in the beam, regardless
        of where the assembly currently is.

        We may also want to move the assembly out of the beam with::

            await aperture_scatterguard.selected_aperture.set(ApertureValue.OUT_OF_BEAM)

        Note, to make sure we do this as quickly as possible, the scatterguard will stay
        in the same position relative to the aperture.

        We may then want to keep the assembly out of the beam whilst asynchronously preparing
        the other axes for the aperture that's to follow::

            await aperture_scatterguard.prepare(ApertureValue.LARGE)

        Then, at a later time, move back into the beam::

            await  aperture_scatterguard.selected_aperture.set(ApertureValue.LARGE)

        Given the prepare has been done this move will now be faster as only the y is
        left to move.
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
        self._loaded_positions = loaded_positions
        self._tolerances = tolerances
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.selected_aperture = derived_signal_rw(
                self._get_current_aperture_position,
                self._set_current_aperture_position,
                large=self.aperture.large,
                medium=self.aperture.medium,
                small=self.aperture.small,
                current_ap_y=self.aperture.y.user_readback,
            )

        self.radius = derived_signal_r(
            self._get_current_radius,
            current_aperture=self.selected_aperture,
            derived_units="µm",
        )

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

        super().__init__(name)

    async def _set_current_aperture_position(self, value: ApertureValue) -> None:
        position = self._loaded_positions[value]
        await self._check_safe_to_move(position.aperture_z)

        if value == ApertureValue.OUT_OF_BEAM:
            out_y = self._loaded_positions[ApertureValue.OUT_OF_BEAM].aperture_y
            await self.aperture.y.set(out_y)
        else:
            await self._safe_move_whilst_in_beam(position)

    async def _check_safe_to_move(self, expected_z_position: float):
        """The assembly is moved (in z) to be under the table when the beamline is not
        in use. If we try and move whilst in the incorrect Z position we will collide
        with the table.

        Additionally, because there are so many collision possibilities in the device we
        throw an error if any of the axes are already moving.
        """
        current_ap_z = await self.aperture.z.user_readback.get_value()
        diff_on_z = abs(current_ap_z - expected_z_position)
        aperture_z_tolerance = self._tolerances.aperture_z
        if diff_on_z > aperture_z_tolerance:
            raise InvalidApertureMove(
                f"Current aperture z ({current_ap_z}), outside of tolerance ({aperture_z_tolerance}) from target ({expected_z_position})."
            )

        all_axes = [
            self.aperture.x,
            self.aperture.y,
            self.aperture.z,
            self.scatterguard.x,
            self.scatterguard.y,
        ]
        for axis in all_axes:
            axis_stationary = await axis.motor_done_move.get_value()
            if not axis_stationary:
                raise InvalidApertureMove(
                    f"{axis.name} is still moving. Wait for it to finish before"
                    "triggering another move."
                )

    def _get_current_radius(self, current_aperture: ApertureValue) -> float:
        return self._loaded_positions[current_aperture].radius

    def _is_out_of_beam(self, current_ap_y: float) -> bool:
        out_ap_y = self._loaded_positions[ApertureValue.OUT_OF_BEAM].aperture_y
        return current_ap_y <= out_ap_y + self._tolerances.aperture_y

    def _get_current_aperture_position(
        self, large: float, medium: float, small: float, current_ap_y: float
    ) -> ApertureValue:
        if large == 1:
            return ApertureValue.LARGE
        elif medium == 1:
            return ApertureValue.MEDIUM
        elif small == 1:
            return ApertureValue.SMALL
        elif self._is_out_of_beam(current_ap_y):
            return ApertureValue.OUT_OF_BEAM

        raise InvalidApertureMove("Current aperture/scatterguard state unrecognised")

    async def _safe_move_whilst_in_beam(self, position: AperturePosition):
        """
        Move the aperture and scatterguard combo safely to a new position.
        See https://github.com/DiamondLightSource/hyperion/wiki/Aperture-Scatterguard-Collisions
        for why this is required. TLDR is that we have a collision at the top of y so we need
        to make sure we move the assembly down before we move the scatterguard up.
        """
        current_ap_y = await self.aperture.y.user_readback.get_value()

        aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = (
            position.values
        )

        if aperture_y > current_ap_y:
            # Assembly needs to move up so move the scatterguard down first
            await asyncio.gather(
                self.scatterguard.x.set(scatterguard_x),
                self.scatterguard.y.set(scatterguard_y),
            )
            await asyncio.gather(
                self.aperture.x.set(aperture_x),
                self.aperture.y.set(aperture_y),
                self.aperture.z.set(aperture_z),
            )
        else:
            await asyncio.gather(
                self.aperture.x.set(aperture_x),
                self.aperture.y.set(aperture_y),
                self.aperture.z.set(aperture_z),
            )

            await asyncio.gather(
                self.scatterguard.x.set(scatterguard_x),
                self.scatterguard.y.set(scatterguard_y),
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

    @AsyncStatus.wrap
    async def prepare(self, value: ApertureValue):
        """Moves the assembly to the position for the specified aperture, whilst keeping
        it out of the beam if it already is so.

        Moving the assembly whilst out of the beam has no collision risk so we can just
        move all the motors together.
        """
        if self._is_out_of_beam(await self.aperture.y.user_readback.get_value()):
            aperture_x, _, aperture_z, scatterguard_x, scatterguard_y = (
                self._loaded_positions[value].values
            )

            await asyncio.gather(
                self.aperture.x.set(aperture_x),
                self.aperture.z.set(aperture_z),
                self.scatterguard.x.set(scatterguard_x),
                self.scatterguard.y.set(scatterguard_y),
            )
        else:
            await self.selected_aperture.set(value)
