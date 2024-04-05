import operator
from collections import namedtuple
from dataclasses import dataclass
from functools import reduce
from typing import List, Sequence

from ophyd import Component as Cpt
from ophyd import SignalRO
from ophyd.epics_motor import EpicsMotor
from ophyd.status import AndStatus, Status, StatusBase

from dodal.devices.aperture import Aperture
from dodal.devices.logging_ophyd_device import InfoLoggingDevice
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
class SingleAperturePosition:
    name: str
    GDA_name: str
    radius_microns: float | None
    location: ApertureFiveDimensionalLocation


def position_from_params(
    name: str, GDA_name: str, radius_microns: float | None, params: dict
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


class ApertureScatterguard(InfoLoggingDevice):
    aperture = Cpt(Aperture, "-MO-MAPT-01:")
    scatterguard = Cpt(Scatterguard, "-MO-SCAT-01:")
    aperture_positions: AperturePositions | None = None
    TOLERANCE_STEPS = 3  # Number of MRES steps

    class SelectedAperture(SignalRO):
        def get(self):
            assert isinstance(self.parent, ApertureScatterguard)
            return self.parent._get_current_aperture_position()

    selected_aperture = Cpt(SelectedAperture)

    def load_aperture_positions(self, positions: AperturePositions):
        LOGGER.info(f"{self.name} loaded in {positions}")
        self.aperture_positions = positions

    def set(self, pos: SingleAperturePosition) -> StatusBase:
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

    def _set_raw_unsafe(self, positions: ApertureFiveDimensionalLocation) -> AndStatus:
        motors: Sequence[EpicsMotor] = self._get_motor_list()
        return reduce(
            operator.and_, [motor.set(pos) for motor, pos in zip(motors, positions)]
        )

    def _get_current_aperture_position(self) -> SingleAperturePosition:
        """
        Returns the current aperture position using readback values
        for SMALL, MEDIUM, LARGE. ROBOT_LOAD position defined when
        mini aperture y <= ROBOT_LOAD.location.aperture_y + tolerance.
        If no position is found then raises InvalidApertureMove.
        """
        assert isinstance(self.aperture_positions, AperturePositions)
        current_ap_y = float(self.aperture.y.user_readback.get())
        robot_load_ap_y = self.aperture_positions.ROBOT_LOAD.location.aperture_y
        tolerance = self.TOLERANCE_STEPS * self.aperture.y.motor_resolution.get()
        if int(self.aperture.large.get()) == 1:
            return self.aperture_positions.LARGE
        elif int(self.aperture.medium.get()) == 1:
            return self.aperture_positions.MEDIUM
        elif int(self.aperture.small.get()) == 1:
            return self.aperture_positions.SMALL
        elif current_ap_y <= robot_load_ap_y + tolerance:
            return self.aperture_positions.ROBOT_LOAD

        raise InvalidApertureMove("Current aperture/scatterguard state unrecognised")

    def _safe_move_within_datacollection_range(
        self, pos: ApertureFiveDimensionalLocation
    ) -> StatusBase:
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

        ap_z_in_position = self.aperture.z.motor_done_move.get()
        if not ap_z_in_position:
            status: Status = Status(obj=self)
            status.set_exception(
                InvalidApertureMove(
                    "ApertureScatterguard z is still moving. Wait for it to finish "
                    "before triggering another move."
                )
            )
            return status

        current_ap_z = self.aperture.z.user_setpoint.get()
        tolerance = self.TOLERANCE_STEPS * self.aperture.z.motor_resolution.get()
        diff_on_z = abs(current_ap_z - aperture_z)
        if diff_on_z > tolerance:
            raise InvalidApertureMove(
                "ApertureScatterguard safe move is not yet defined for positions "
                "outside of LARGE, MEDIUM, SMALL, ROBOT_LOAD. "
                f"Current aperture z ({current_ap_z}), outside of tolerance ({tolerance}) from target ({aperture_z})."
            )

        current_ap_y = self.aperture.y.user_readback.get()
        if aperture_y > current_ap_y:
            sg_status: AndStatus = self.scatterguard.x.set(
                scatterguard_x
            ) & self.scatterguard.y.set(scatterguard_y)
            sg_status.wait()
            return (
                sg_status
                & self.aperture.x.set(aperture_x)
                & self.aperture.y.set(aperture_y)
                & self.aperture.z.set(aperture_z)
            )

        ap_status: AndStatus = (
            self.aperture.x.set(aperture_x)
            & self.aperture.y.set(aperture_y)
            & self.aperture.z.set(aperture_z)
        )
        ap_status.wait()
        final_status: AndStatus = (
            ap_status
            & self.scatterguard.x.set(scatterguard_x)
            & self.scatterguard.y.set(scatterguard_y)
        )
        return final_status
