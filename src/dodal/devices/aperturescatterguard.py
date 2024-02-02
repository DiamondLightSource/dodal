from collections import namedtuple
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from ophyd import Component as Cpt
from ophyd import Signal
from ophyd.status import AndStatus, Status

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
    radius_microns: int | None
    location: ApertureFiveDimensionalLocation


@dataclass
class AperturePositions:
    """Holds the motor positions needed to select a particular aperture size."""

    LARGE: SingleAperturePosition
    MEDIUM: SingleAperturePosition
    SMALL: SingleAperturePosition
    ROBOT_LOAD: SingleAperturePosition

    # one micrometre tolerance
    TOLERANCE_MM: float = 0.001

    @classmethod
    def from_gda_beamline_params(cls, params):
        return cls(
            LARGE=SingleAperturePosition(
                "Large",
                100,
                ApertureFiveDimensionalLocation(
                    params["miniap_x_LARGE_APERTURE"],
                    params["miniap_y_LARGE_APERTURE"],
                    params["miniap_z_LARGE_APERTURE"],
                    params["sg_x_LARGE_APERTURE"],
                    params["sg_y_LARGE_APERTURE"],
                ),
            ),
            MEDIUM=SingleAperturePosition(
                "Medium",
                50,
                ApertureFiveDimensionalLocation(
                    params["miniap_x_MEDIUM_APERTURE"],
                    params["miniap_y_MEDIUM_APERTURE"],
                    params["miniap_z_MEDIUM_APERTURE"],
                    params["sg_x_MEDIUM_APERTURE"],
                    params["sg_y_MEDIUM_APERTURE"],
                ),
            ),
            SMALL=SingleAperturePosition(
                "Small",
                20,
                ApertureFiveDimensionalLocation(
                    params["miniap_x_SMALL_APERTURE"],
                    params["miniap_y_SMALL_APERTURE"],
                    params["miniap_z_SMALL_APERTURE"],
                    params["sg_x_SMALL_APERTURE"],
                    params["sg_y_SMALL_APERTURE"],
                ),
            ),
            ROBOT_LOAD=SingleAperturePosition(
                "Robot load",
                None,
                ApertureFiveDimensionalLocation(
                    params["miniap_x_ROBOT_LOAD"],
                    params["miniap_y_ROBOT_LOAD"],
                    params["miniap_z_ROBOT_LOAD"],
                    params["sg_x_ROBOT_LOAD"],
                    params["sg_y_ROBOT_LOAD"],
                ),
            ),
        )

    def get_new_position(
        self, pos: ApertureFiveDimensionalLocation
    ) -> SingleAperturePosition:
        """
        Check if argument 'pos' is a valid position in this AperturePositions object.
        """
        options: List[SingleAperturePosition] = [
            self.LARGE,
            self.MEDIUM,
            self.SMALL,
            self.ROBOT_LOAD,
        ]
        for obj in options:
            if np.allclose(obj.location, pos, atol=self.TOLERANCE_MM):
                return obj
        return None


class ApertureScatterguard(InfoLoggingDevice):
    aperture = Cpt(Aperture, "-MO-MAPT-01:")
    scatterguard = Cpt(Scatterguard, "-MO-SCAT-01:")
    aperture_positions: Optional[AperturePositions] = None
    selected_aperture = Cpt(Signal)
    APERTURE_Z_TOLERANCE = 3  # Number of MRES steps

    def load_aperture_positions(self, positions: AperturePositions):
        LOGGER.info(f"{self.name} loaded in {positions}")
        self.aperture_positions = positions

    def set(self, pos: ApertureFiveDimensionalLocation) -> AndStatus:
        new_selected_aperture: SingleAperturePosition | None = None
        try:
            # make sure that the reference values are loaded
            assert isinstance(self.aperture_positions, AperturePositions)
            # get the new aperture obrect
            new_selected_aperture = self.aperture_positions.get_new_position(pos)
            assert new_selected_aperture is not None
        except AssertionError as e:
            raise InvalidApertureMove(repr(e))

        self.selected_aperture.set(new_selected_aperture)
        return self._safe_move_within_datacollection_range(
            new_selected_aperture.location
        )

    def _safe_move_within_datacollection_range(
        self, pos: ApertureFiveDimensionalLocation
    ) -> AndStatus | Status:
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

        # CASE still moving
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

        # CASE invalid target position
        current_ap_z = self.aperture.z.user_setpoint.get()
        tolerance = self.APERTURE_Z_TOLERANCE * self.aperture.z.motor_resolution.get()
        diff_on_z = abs(current_ap_z - aperture_z)
        if diff_on_z > tolerance:
            raise InvalidApertureMove(
                "ApertureScatterguard safe move is not yet defined for positions "
                "outside of LARGE, MEDIUM, SMALL, ROBOT_LOAD. "
                f"Current aperture z ({current_ap_z}), outside of tolerance ({tolerance}) from target ({aperture_z})."
            )

        # CASE moves along Z
        current_ap_y = self.aperture.y.user_readback.get()
        if aperture_y > current_ap_y:
            sg_status: AndStatus = self.scatterguard.x.set(
                scatterguard_x
            ) & self.scatterguard.y.set(scatterguard_y)
            sg_status.wait()
            final_status: AndStatus = (
                sg_status
                & self.aperture.x.set(aperture_x)
                & self.aperture.y.set(aperture_y)
                & self.aperture.z.set(aperture_z)
            )
            return final_status

        # CASE does not move along Z
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
