import asyncio
from collections import OrderedDict, namedtuple
from dataclasses import asdict, dataclass
from enum import Enum

from bluesky.protocols import Movable, Reading
from ophyd_async.core import AsyncStatus, SignalR, StandardReadable
from ophyd_async.core.soft_signal_backend import SoftConverter, SoftSignalBackend

from dodal.devices.aperture import Aperture
from dodal.devices.scatterguard import Scatterguard
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
class ApertureScatterguardTolerances:
    ap_x: float
    ap_y: float
    ap_z: float
    sg_x: float
    sg_y: float


@dataclass
class SingleAperturePosition:
    # Default values are needed as ophyd_async sim does not respect initial_values of
    # soft signal backends see https://github.com/bluesky/ophyd-async/issues/266
    name: str = ""
    GDA_name: str = ""
    radius_microns: float | None = None
    location: ApertureFiveDimensionalLocation = ApertureFiveDimensionalLocation(
        0, 0, 0, 0, 0
    )


# Use StrEnum once we stop python 3.10 support
class AperturePositionGDANames(str, Enum):
    LARGE_APERTURE = "LARGE_APERTURE"
    MEDIUM_APERTURE = "MEDIUM_APERTURE"
    SMALL_APERTURE = "SMALL_APERTURE"
    ROBOT_LOAD = "ROBOT_LOAD"

    def __str__(self):
        return str(self.value)


def position_from_params(
    name: str,
    GDA_name: AperturePositionGDANames,
    radius_microns: float | None,
    params: dict,
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


def tolerances_from_params(params: dict) -> ApertureScatterguardTolerances:
    return ApertureScatterguardTolerances(
        ap_x=params["miniap_x_tolerance"],
        ap_y=params["miniap_y_tolerance"],
        ap_z=params["miniap_z_tolerance"],
        sg_x=params["sg_x_tolerance"],
        sg_y=params["sg_y_tolerance"],
    )


@dataclass
class AperturePositions:
    """Holds the motor positions needed to select a particular aperture size. This class should be instantiated with definitions for its sizes
    using from_gda_beamline_params"""

    LARGE: SingleAperturePosition
    MEDIUM: SingleAperturePosition
    SMALL: SingleAperturePosition
    ROBOT_LOAD: SingleAperturePosition

    tolerances: ApertureScatterguardTolerances

    UNKNOWN = SingleAperturePosition(
        "Unknown", "UNKNOWN", None, ApertureFiveDimensionalLocation(0, 0, 0, 0, 0)
    )

    @classmethod
    def from_gda_beamline_params(cls, params):
        return cls(
            LARGE=position_from_params(
                "Large", AperturePositionGDANames.LARGE_APERTURE, 100, params
            ),
            MEDIUM=position_from_params(
                "Medium", AperturePositionGDANames.MEDIUM_APERTURE, 50, params
            ),
            SMALL=position_from_params(
                "Small", AperturePositionGDANames.SMALL_APERTURE, 20, params
            ),
            ROBOT_LOAD=position_from_params(
                "Robot load", AperturePositionGDANames.ROBOT_LOAD, None, params
            ),
            tolerances=tolerances_from_params(params),
        )

    def get_position_from_gda_aperture_name(
        self, gda_aperture_name: AperturePositionGDANames
    ) -> SingleAperturePosition:
        apertures = [ap for ap in self.as_list() if ap.GDA_name == gda_aperture_name]
        if not apertures:
            raise ValueError(
                f"Tried to convert unknown aperture name {gda_aperture_name} to a SingleAperturePosition"
            )
        else:
            return apertures[0]

    def as_list(self) -> list[SingleAperturePosition]:
        return [
            self.LARGE,
            self.MEDIUM,
            self.SMALL,
            self.ROBOT_LOAD,
        ]


class ApertureScatterguard(StandardReadable, Movable):
    def __init__(self, prefix: str = "", name: str = "") -> None:
        self.aperture = Aperture(prefix + "-MO-MAPT-01:")
        self.scatterguard = Scatterguard(prefix + "-MO-SCAT-01:")
        self.aperture_positions: AperturePositions | None = None
        self.TOLERANCE_STEPS = 3  # Number of MRES steps
        aperture_backend = SoftSignalBackend(
            SingleAperturePosition, AperturePositions.UNKNOWN
        )
        aperture_backend.converter = self.ApertureConverter()
        self.selected_aperture = self.SelectedAperture(backend=aperture_backend)
        self.set_readable_signals(
            read=[
                self.selected_aperture,
            ]
        )
        super().__init__(name)

    class ApertureConverter(SoftConverter):
        # Ophyd-async #311 should add a default converter for dataclasses to do this
        def reading(
            self, value: SingleAperturePosition, timestamp: float, severity: int
        ) -> Reading:
            return Reading(
                value=asdict(value),
                timestamp=timestamp,
                alarm_severity=-1 if severity > 2 else severity,
            )

    class SelectedAperture(SignalR):
        async def read(self, *args, **kwargs):
            assert isinstance(self.parent, ApertureScatterguard)
            await self._backend.put(await self.parent._get_current_aperture_position())
            return {self.name: await self._backend.get_reading()}

        async def describe(self):
            return OrderedDict(
                [
                    (
                        self._name,
                        {
                            "source": self._backend.source(self._name),  # type: ignore
                            "dtype": "array",
                            "shape": [
                                -1,
                            ],  # TODO describe properly - see https://github.com/DiamondLightSource/dodal/issues/253
                        },
                    ),
                ],
            )

    def load_aperture_positions(self, positions: AperturePositions):
        LOGGER.info(f"{self.name} loaded in {positions}")
        self.aperture_positions = positions

    def set(self, pos: SingleAperturePosition) -> AsyncStatus:
        assert isinstance(self.aperture_positions, AperturePositions)
        if pos not in self.aperture_positions.as_list():
            raise InvalidApertureMove(f"Unknown aperture: {pos}")

        return AsyncStatus(self._safe_move_within_datacollection_range(pos.location))

    def _get_motor_list(self):
        return [
            self.aperture.x,
            self.aperture.y,
            self.aperture.z,
            self.scatterguard.x,
            self.scatterguard.y,
        ]

    @AsyncStatus.wrap
    async def _set_raw_unsafe(self, positions: ApertureFiveDimensionalLocation):
        """Accept the risks and move in an unsafe way. Collisions possible."""

        # unpacking the position
        aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = positions

        await asyncio.gather(
            self.aperture.x.set(aperture_x),
            self.aperture.y.set(aperture_y),
            self.aperture.z.set(aperture_z),
            self.scatterguard.x.set(scatterguard_x),
            self.scatterguard.y.set(scatterguard_y),
        )

    async def _get_current_aperture_position(self) -> SingleAperturePosition:
        """
        Returns the current aperture position using readback values
        for SMALL, MEDIUM, LARGE. ROBOT_LOAD position defined when
        mini aperture y <= ROBOT_LOAD.location.aperture_y + tolerance.
        If no position is found then raises InvalidApertureMove.
        """
        assert isinstance(self.aperture_positions, AperturePositions)
        current_ap_y = await self.aperture.y.user_readback.get_value(cached=False)
        robot_load_ap_y = self.aperture_positions.ROBOT_LOAD.location.aperture_y
        if await self.aperture.large.get_value(cached=False) == 1:
            return self.aperture_positions.LARGE
        elif await self.aperture.medium.get_value(cached=False) == 1:
            return self.aperture_positions.MEDIUM
        elif await self.aperture.small.get_value(cached=False) == 1:
            return self.aperture_positions.SMALL
        elif current_ap_y <= robot_load_ap_y + self.aperture_positions.tolerances.ap_y:
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
        assert self.aperture_positions is not None
        # unpacking the position
        aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = pos

        ap_z_in_position = await self.aperture.z.motor_done_move.get_value()
        if not ap_z_in_position:
            raise InvalidApertureMove(
                "ApertureScatterguard z is still moving. Wait for it to finish "
                "before triggering another move."
            )

        current_ap_z = await self.aperture.z.user_readback.get_value()
        diff_on_z = abs(current_ap_z - aperture_z)
        if diff_on_z > self.aperture_positions.tolerances.ap_z:
            raise InvalidApertureMove(
                "ApertureScatterguard safe move is not yet defined for positions "
                "outside of LARGE, MEDIUM, SMALL, ROBOT_LOAD. "
                f"Current aperture z ({current_ap_z}), outside of tolerance ({self.aperture_positions.tolerances.ap_z}) from target ({aperture_z})."
            )

        current_ap_y = await self.aperture.y.user_readback.get_value()

        if aperture_y > current_ap_y:
            await asyncio.gather(
                self.scatterguard.x.set(scatterguard_x),
                self.scatterguard.y.set(scatterguard_y),
            )
            await asyncio.gather(
                self.aperture.x.set(aperture_x),
                self.aperture.y.set(aperture_y),
                self.aperture.z.set(aperture_z),
            )
            return
        await asyncio.gather(
            self.aperture.x.set(aperture_x),
            self.aperture.y.set(aperture_y),
            self.aperture.z.set(aperture_z),
        )

        await asyncio.gather(
            self.scatterguard.x.set(scatterguard_x),
            self.scatterguard.y.set(scatterguard_y),
        )
