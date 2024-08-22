import asyncio
from collections import namedtuple
from dataclasses import asdict, dataclass
from enum import Enum

from bluesky.protocols import Movable, Reading
from event_model.documents.event_descriptor import DataKey
from ophyd_async.core import AsyncStatus, HintedSignal, SignalR, StandardReadable
from ophyd_async.core.soft_signal_backend import SoftConverter, SoftSignalBackend

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.aperture import Aperture
from dodal.devices.scatterguard import Scatterguard


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
    name: str
    GDA_name: str
    radius_microns: float | None
    location: ApertureFiveDimensionalLocation


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
    params: GDABeamlineParameters,
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


def load_tolerances_from_beamline_params(
    params: GDABeamlineParameters,
) -> ApertureScatterguardTolerances:
    return ApertureScatterguardTolerances(
        ap_x=params["miniap_x_tolerance"],
        ap_y=params["miniap_y_tolerance"],
        ap_z=params["miniap_z_tolerance"],
        sg_x=params["sg_x_tolerance"],
        sg_y=params["sg_y_tolerance"],
    )


class AperturePosition(Enum):
    ROBOT_LOAD = 0
    SMALL = 1
    MEDIUM = 2
    LARGE = 3


def load_positions_from_beamline_parameters(
    params: GDABeamlineParameters,
) -> dict[AperturePosition, SingleAperturePosition]:
    return {
        AperturePosition.ROBOT_LOAD: position_from_params(
            "Robot load", AperturePositionGDANames.ROBOT_LOAD, None, params
        ),
        AperturePosition.SMALL: position_from_params(
            "Small", AperturePositionGDANames.SMALL_APERTURE, 20, params
        ),
        AperturePosition.MEDIUM: position_from_params(
            "Medium", AperturePositionGDANames.MEDIUM_APERTURE, 50, params
        ),
        AperturePosition.LARGE: position_from_params(
            "Large", AperturePositionGDANames.LARGE_APERTURE, 100, params
        ),
    }


class ApertureScatterguard(StandardReadable, Movable):
    def __init__(
        self,
        loaded_positions: dict[AperturePosition, SingleAperturePosition],
        tolerances: ApertureScatterguardTolerances,
        prefix: str = "",
        name: str = "",
    ) -> None:
        self._aperture = Aperture(prefix + "-MO-MAPT-01:")
        self._scatterguard = Scatterguard(prefix + "-MO-SCAT-01:")
        self._loaded_positions = loaded_positions
        self._tolerances = tolerances
        aperture_backend = SoftSignalBackend(
            SingleAperturePosition, self._loaded_positions[AperturePosition.ROBOT_LOAD]
        )
        aperture_backend.converter = self.ApertureConverter()
        self.selected_aperture = self.SelectedAperture(backend=aperture_backend)
        self.add_readables([self.selected_aperture], wrapper=HintedSignal)
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
            assert self._backend
            await self._backend.put(await self.parent.get_current_aperture_position())
            return {self.name: await self._backend.get_reading()}

        async def describe(self) -> dict[str, DataKey]:
            return {
                self._name: DataKey(
                    dtype="array",
                    shape=[
                        -1,
                    ],  # TODO describe properly - see https://github.com/DiamondLightSource/dodal/issues/253,
                    source=self._backend.source(self._name),  # type: ignore
                )
            }

    def get_position_from_gda_aperture_name(
        self, gda_aperture_name: AperturePositionGDANames
    ) -> AperturePosition:
        for aperture, detail in self._loaded_positions.items():
            if detail.GDA_name == gda_aperture_name:
                return aperture
        raise ValueError(
            f"Tried to convert unknown aperture name {gda_aperture_name} to a SingleAperturePosition"
        )

    def get_gda_name_for_position(self, position: AperturePosition) -> str:
        detailed_position = self._loaded_positions[position]
        return detailed_position.GDA_name

    @AsyncStatus.wrap
    async def set(self, value: AperturePosition):
        position = self._loaded_positions[value]
        await self._safe_move_within_datacollection_range(position.location)

    def _get_motor_list(self):
        return [
            self._aperture.x,
            self._aperture.y,
            self._aperture.z,
            self._scatterguard.x,
            self._scatterguard.y,
        ]

    @AsyncStatus.wrap
    async def _set_raw_unsafe(self, positions: ApertureFiveDimensionalLocation):
        """Accept the risks and move in an unsafe way. Collisions possible."""

        # unpacking the position
        aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = positions

        await asyncio.gather(
            self._aperture.x.set(aperture_x),
            self._aperture.y.set(aperture_y),
            self._aperture.z.set(aperture_z),
            self._scatterguard.x.set(scatterguard_x),
            self._scatterguard.y.set(scatterguard_y),
        )

    async def get_current_aperture_position(self) -> SingleAperturePosition:
        """
        Returns the current aperture position using readback values
        for SMALL, MEDIUM, LARGE. ROBOT_LOAD position defined when
        mini aperture y <= ROBOT_LOAD.location.aperture_y + tolerance.
        If no position is found then raises InvalidApertureMove.
        """
        current_ap_y = await self._aperture.y.user_readback.get_value(cached=False)
        robot_load_ap_y = self._loaded_positions[
            AperturePosition.ROBOT_LOAD
        ].location.aperture_y
        if await self._aperture.large.get_value(cached=False) == 1:
            return self._loaded_positions[AperturePosition.LARGE]
        elif await self._aperture.medium.get_value(cached=False) == 1:
            return self._loaded_positions[AperturePosition.MEDIUM]
        elif await self._aperture.small.get_value(cached=False) == 1:
            return self._loaded_positions[AperturePosition.SMALL]
        elif current_ap_y <= robot_load_ap_y + self._tolerances.ap_y:
            return self._loaded_positions[AperturePosition.ROBOT_LOAD]

        raise InvalidApertureMove("Current aperture/scatterguard state unrecognised")

    async def _safe_move_within_datacollection_range(
        self, pos: ApertureFiveDimensionalLocation
    ):
        """
        Move the aperture and scatterguard combo safely to a new position.
        See https://github.com/DiamondLightSource/hyperion/wiki/Aperture-Scatterguard-Collisions
        for why this is required.
        """
        assert self._loaded_positions is not None
        # unpacking the position
        aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = pos

        ap_z_in_position = await self._aperture.z.motor_done_move.get_value()
        if not ap_z_in_position:
            raise InvalidApertureMove(
                "ApertureScatterguard z is still moving. Wait for it to finish "
                "before triggering another move."
            )

        current_ap_z = await self._aperture.z.user_readback.get_value()
        diff_on_z = abs(current_ap_z - aperture_z)
        if diff_on_z > self._tolerances.ap_z:
            raise InvalidApertureMove(
                "ApertureScatterguard safe move is not yet defined for positions "
                "outside of LARGE, MEDIUM, SMALL, ROBOT_LOAD. "
                f"Current aperture z ({current_ap_z}), outside of tolerance ({self._tolerances.ap_z}) from target ({aperture_z})."
            )

        current_ap_y = await self._aperture.y.user_readback.get_value()

        if aperture_y > current_ap_y:
            await asyncio.gather(
                self._scatterguard.x.set(scatterguard_x),
                self._scatterguard.y.set(scatterguard_y),
            )
            await asyncio.gather(
                self._aperture.x.set(aperture_x),
                self._aperture.y.set(aperture_y),
                self._aperture.z.set(aperture_z),
            )
            return
        await asyncio.gather(
            self._aperture.x.set(aperture_x),
            self._aperture.y.set(aperture_y),
            self._aperture.z.set(aperture_z),
        )

        await asyncio.gather(
            self._scatterguard.x.set(scatterguard_x),
            self._scatterguard.y.set(scatterguard_y),
        )
