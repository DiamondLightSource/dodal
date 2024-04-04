import asyncio
import operator
from collections import namedtuple
from dataclasses import dataclass
from functools import reduce
from typing import List, Optional, Sequence

from ophyd_async.core import AsyncStatus, SignalR, StandardReadable
from ophyd_async.core.sim_signal_backend import SimSignalBackend

from dodal.devices.aperture import Aperture
from dodal.devices.scatterguard import Scatterguard
from dodal.devices.util.motor_utils import ExtendedMotor
from dodal.log import LOGGER


class InvalidApertureMove(Exception):
    pass


ApertureFiveDimensionalLocation = namedtuple(
    "ApertureFiveDimensionalLocation",
    [
        "aperture_x",
        "aperture_y",
        "aperture_z",
        "scatterguard_x",
        "scatterguard_y",
    ],
)


@dataclass
class SingleAperturePosition:
    name: str = ""
    GDA_name: str = ""
    radius_microns: Optional[float] = 0
    location: ApertureFiveDimensionalLocation = ApertureFiveDimensionalLocation(
        0, 0, 0, 0, 0
    )


def position_from_params(
    name: str, GDA_name: str, radius_microns: Optional[float], params: dict
) -> SingleAperturePosition:
    return SingleAperturePosition(
        name,
        GDA_name,
        radius_microns,
        ApertureFiveDimensionalLocation(
            params[f"miniap_x_{GDA_name}"],
            params[f"miniap_y_{GDA_name}"],
            params[f"miniap_z_{GDA_name}"],
            params[f"sg_x_{GDA_name}"],
            params[f"sg_y_{GDA_name}"],
        ),
    )


@dataclass
class AperturePositions:
    """Holds the motor positions needed to select a particular aperture size."""

    LARGE: SingleAperturePosition
    MEDIUM: SingleAperturePosition
    SMALL: SingleAperturePosition
    ROBOT_LOAD: SingleAperturePosition

    @classmethod
    def from_gda_beamline_params(cls, params):
        return cls(
            LARGE=position_from_params("Large", "LARGE_APERTURE", 100, params),
            MEDIUM=position_from_params("Medium", "MEDIUM_APERTURE", 50, params),
            SMALL=position_from_params("Small", "SMALL_APERTURE", 20, params),
            ROBOT_LOAD=position_from_params("Robot load", "ROBOT_LOAD", None, params),
        )

    def as_list(self) -> List[SingleAperturePosition]:
        return [
            self.LARGE,
            self.MEDIUM,
            self.SMALL,
            self.ROBOT_LOAD,
        ]


class ApertureScatterguard(StandardReadable):
    def __init__(self, prefix: str = "", name: str = "") -> None:
        self.aperture = Aperture(prefix="-MO-MAPT-01:")
        self.scatterguard = Scatterguard(prefix="-MO-SCAT-01:")
        self.aperture_positions: Optional[AperturePositions] = None
        self.TOLERANCE_STEPS = 3  # Number of MRES steps
        self.selected_aperture = self.SelectedAperture(
            backend=SimSignalBackend(datatype=SingleAperturePosition, source="")
        )
        self.set_readable_signals(
            read=[
                self.selected_aperture,
            ]
        )
        super().__init__(name)

    class SelectedAperture(SignalR):
        async def read(self, *args, **kwargs):
            assert isinstance(self.parent, ApertureScatterguard)
            await self._backend.put(await self.parent._get_current_aperture_position())
            return {self.name: await self._backend.get_reading()}

    def load_aperture_positions(self, positions: AperturePositions):
        LOGGER.info(f"{self.name} loaded in {positions}")
        self.aperture_positions = positions

    def set(self, pos: SingleAperturePosition):
        assert isinstance(self.aperture_positions, AperturePositions)
        if pos not in self.aperture_positions.as_list():
            raise InvalidApertureMove(f"Unknown aperture: {pos}")

        return self._safe_move_within_datacollection_range(pos.location)

    def _get_motor_list(self):
        return [
            self.aperture.x,
            self.aperture.y,
            self.aperture.z,
            self.scatterguard.x,
            self.scatterguard.y,
        ]

    async def _set_raw_unsafe(self, positions: ApertureFiveDimensionalLocation):
        """Accept the risks and move in an unsafe way. Collisions possible."""

        # unpacking the position
        aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = positions

        await asyncio.gather(
            self.aperture.x._move(aperture_x),
            self.aperture.y._move(aperture_y),
            self.aperture.z._move(aperture_z),
            self.scatterguard.x._move(scatterguard_x),
            self.scatterguard.y._move(scatterguard_y),
        )

    async def _get_current_aperture_position(self) -> SingleAperturePosition:
        """
        Returns the current aperture position using readback values
        for SMALL, MEDIUM, LARGE. ROBOT_LOAD position defined when
        mini aperture y <= ROBOT_LOAD.location.aperture_y + tolerance.
        If no position is found then raises InvalidApertureMove.
        """
        assert isinstance(self.aperture_positions, AperturePositions)
        current_ap_y = await self.aperture.y.readback.get_value(cached=False)
        robot_load_ap_y = self.aperture_positions.ROBOT_LOAD.location.aperture_y
        tolerance = (
            self.TOLERANCE_STEPS * await self.aperture.y.motor_resolution.get_value()
        )
        # extendedepicsmotor class has tolerance fields added
        # ophyd-async epics motor may need to do the same thing - epics motor
        if await self.aperture.large.get_value(cached=False) == 1:
            return self.aperture_positions.LARGE
        elif await self.aperture.medium.get_value(cached=False) == 1:
            return self.aperture_positions.MEDIUM
        elif await self.aperture.small.get_value(cached=False) == 1:
            return self.aperture_positions.SMALL
        elif current_ap_y <= robot_load_ap_y + tolerance:
            return self.aperture_positions.ROBOT_LOAD

        raise InvalidApertureMove("Current aperture/scatterguard state unrecognised")

    async def _safe_move_within_datacollection_range(
        self, pos: ApertureFiveDimensionalLocation
    ):
        """
        Move the aperture and scatterguard combo safely to a new position.
        See https://github.com/DiamondLightSource/hyperion/wiki/Aperture-Scatterguard-Collisions
        for why this is required.
        """
        # EpicsMotor does not have deadband/MRES field, so the way to check if we are
        # in a datacollection position is to see if we are "ready" (DMOV) and the target
        # position is correct

        # unpacking the position
        aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = pos

        ap_z_in_position = await self.aperture.z.motor_done_move.get_value()
        if not ap_z_in_position:
            raise InvalidApertureMove(
                "ApertureScatterguard z is still moving. Wait for it to finish "
                "before triggering another move."
            )

        current_ap_z = await self.aperture.z.readback.get_value()
        tolerance = (
            self.TOLERANCE_STEPS * await self.aperture.z.motor_resolution.get_value()
        )
        diff_on_z = abs(current_ap_z - aperture_z)
        if diff_on_z > tolerance:
            raise InvalidApertureMove(
                "ApertureScatterguard safe move is not yet defined for positions "
                "outside of LARGE, MEDIUM, SMALL, ROBOT_LOAD. "
                f"Current aperture z ({current_ap_z}), outside of tolerance ({tolerance}) from target ({aperture_z})."
            )

        current_ap_y = await self.aperture.y.readback.get_value()

        if aperture_y > current_ap_y:
            await asyncio.gather(
                self.scatterguard.x._move(scatterguard_x),
                self.scatterguard.y._move(scatterguard_y),
            )
            await asyncio.gather(
                self.aperture.x._move(aperture_x),
                self.aperture.y._move(aperture_y),
                self.aperture.z._move(aperture_z),
            )
            return
        await asyncio.gather(
            self.aperture.x._move(aperture_x),
            self.aperture.y._move(aperture_y),
            self.aperture.z._move(aperture_z),
        )

        await asyncio.gather(
            self.scatterguard.x._move(scatterguard_x),
            self.scatterguard.y._move(scatterguard_y),
        )
