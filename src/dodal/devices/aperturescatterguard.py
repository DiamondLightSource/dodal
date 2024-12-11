from __future__ import annotations

import asyncio

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
)
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


class ApertureScatterguard(StandardReadable, Movable):
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

        super().__init__(name)

    def get_position_from_gda_aperture_name(
        self, gda_aperture_name: str
    ) -> ApertureValue:
        return ApertureValue(gda_aperture_name)

    @AsyncStatus.wrap
    async def set(self, value: ApertureValue):
        position = self._loaded_positions[value]
        await self._safe_move_within_datacollection_range(position, value)

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

    async def _get_current_aperture_position(self) -> ApertureValue:
        """
        Returns the current aperture position using readback values
        for SMALL, MEDIUM, LARGE. ROBOT_LOAD position defined when
        mini aperture y <= ROBOT_LOAD.location.aperture_y + tolerance.
        If no position is found then raises InvalidApertureMove.
        """
        current_ap_y = await self.aperture.y.user_readback.get_value(cached=False)
        robot_load_ap_y = self._loaded_positions[ApertureValue.ROBOT_LOAD].aperture_y
        if await self.aperture.large.get_value(cached=False) == 1:
            return ApertureValue.LARGE
        elif await self.aperture.medium.get_value(cached=False) == 1:
            return ApertureValue.MEDIUM
        elif await self.aperture.small.get_value(cached=False) == 1:
            return ApertureValue.SMALL
        elif current_ap_y <= robot_load_ap_y + self._tolerances.aperture_y:
            return ApertureValue.ROBOT_LOAD

        raise InvalidApertureMove("Current aperture/scatterguard state unrecognised")

    async def _get_current_radius(self) -> float:
        current_value = await self._get_current_aperture_position()
        return self._loaded_positions[current_value].radius

    async def _safe_move_within_datacollection_range(
        self, position: AperturePosition, value: ApertureValue
    ):
        """
        Move the aperture and scatterguard combo safely to a new position.
        See https://github.com/DiamondLightSource/hyperion/wiki/Aperture-Scatterguard-Collisions
        for why this is required.
        """
        assert self._loaded_positions is not None

        ap_z_in_position = await self.aperture.z.motor_done_move.get_value()
        if not ap_z_in_position:
            raise InvalidApertureMove(
                "ApertureScatterguard z is still moving. Wait for it to finish "
                "before triggering another move."
            )

        current_ap_z = await self.aperture.z.user_readback.get_value()
        diff_on_z = abs(current_ap_z - position.aperture_z)
        if diff_on_z > self._tolerances.aperture_z:
            raise InvalidApertureMove(
                "ApertureScatterguard safe move is not yet defined for positions "
                "outside of LARGE, MEDIUM, SMALL, ROBOT_LOAD. "
                f"Current aperture z ({current_ap_z}), outside of tolerance ({self._tolerances.aperture_z}) from target ({position.aperture_z})."
            )

        current_ap_y = await self.aperture.y.user_readback.get_value()

        aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = (
            position.values
        )

        if position.aperture_y > current_ap_y:
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
