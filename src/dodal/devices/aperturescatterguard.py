from collections import namedtuple
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from ophyd import Component as Cpt
from ophyd import Signal
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


def create_location_from_params(
    GDA_location_name: str, params: dict
) -> ApertureFiveDimensionalLocation:
    return ApertureFiveDimensionalLocation(
        params[f"miniap_x_{GDA_location_name}"],
        params[f"miniap_y_{GDA_location_name}"],
        params[f"miniap_z_{GDA_location_name}"],
        params[f"sg_x_{GDA_location_name}"],
        params[f"sg_y_{GDA_location_name}"],
    )


@dataclass
class SingleAperturePosition:
    name: str
    radius_microns: Optional[int]
    location: ApertureFiveDimensionalLocation


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
            LARGE=SingleAperturePosition(
                "Large", 100, create_location_from_params("LARGE_APERTURE", params)
            ),
            MEDIUM=SingleAperturePosition(
                "Medium", 50, create_location_from_params("MEDIUM_APERTURE", params)
            ),
            SMALL=SingleAperturePosition(
                "Small", 20, create_location_from_params("SMALL_APERTURE", params)
            ),
            ROBOT_LOAD=SingleAperturePosition(
                "Robot load", None, create_location_from_params("ROBOT_LOAD", params)
            ),
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
    aperture_positions: Optional[AperturePositions] = None
    TOLERANCE_STEPS = 3  # Number of MRES steps

    def load_aperture_positions(self, positions: AperturePositions):
        LOGGER.info(f"{self.name} loaded in {positions}")
        self.aperture_positions = positions

    def set(self, pos: SingleAperturePosition) -> StatusBase:
        assert isinstance(self.aperture_positions, AperturePositions)
        if pos not in self.aperture_positions.as_list():
            raise InvalidApertureMove(f"Unknown aperture: {pos}")

        return self._safe_move_within_datacollection_range(pos.location)

    def _get_closest_position_to_current(self) -> SingleAperturePosition:
        """
        Returns the closest valid position to current position within {TOLERANCE_STEPS}.
        If no position is found then raises InvalidApertureMove.
        """
        assert isinstance(self.aperture_positions, AperturePositions)
        for aperture in self.aperture_positions.as_list():
            aperture_in_tolerence = []
            motors = [
                self.aperture.x,
                self.aperture.y,
                self.aperture.z,
                self.scatterguard.x,
                self.scatterguard.y,
            ]
            for motor, test_position in zip(motors, list(aperture.location)):
                current_position = motor.user_readback.get()
                tolerance = self.TOLERANCE_STEPS * motor.motor_resolution.get()
                diff = abs(current_position - test_position)
                aperture_in_tolerence.append(diff <= tolerance)
            if np.all(aperture_in_tolerence):
                return aperture

        raise InvalidApertureMove("Current aperture/scatterguard state unrecognised")

    def read(self):
        selected_aperture = Signal(name=f"{self.name}_selected_aperture")
        assert isinstance(self.aperture_positions, AperturePositions)
        current_aperture = self._get_closest_position_to_current()
        selected_aperture.put(current_aperture)
        res = super().read()
        res.update(selected_aperture.read())
        return res

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
