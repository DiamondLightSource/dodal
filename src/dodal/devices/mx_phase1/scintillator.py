from math import isclose

import bluesky.plan_stubs as bps
from bluesky.utils import MsgGenerator
from ophyd_async.core import StandardReadable, StrictEnum, derived_signal_r
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.mx_phase1.aperturescatterguard import (
    ApertureScatterguard,
    do_with_aperture_scatterguard_in_scin_move_position,
)
from dodal.devices.mx_phase1.beamstop import Beamstop, BeamstopPositions


class InOut(StrictEnum):
    """Moves scintillator in and out of the beam."""

    OUT = "Out"  # Out of beam
    IN = "In"  # In to beam
    UNKNOWN = "Unknown"


class Scintillator(StandardReadable):
    """Moves a scintillator into and out of the beam.

    The scintillator will light up when hit with xrays, this allows scientists to use it
    in conjunction with the optical OAV camera to commission the beamline.

    When moved out of the beam it is parked under the table. This parking has a potential
    to collide with the aperture/scatterguard if that is not correctly parked already.

    The scintillator does not supports reading the current position but not writing to it;
    due to potential collisions with the aperture-scatterguard. Instead a bluesky plan is provided
    which moves the aperture-scatterguard to a safe position for the duration of the move.
    """

    def __init__(
        self,
        prefix: str,
        beamline_parameters: GDABeamlineParameters,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.y_mm = Motor(f"{prefix}Y")
            self.z_mm = Motor(f"{prefix}Z")
            self.selected_pos = derived_signal_r(
                self._get_selected_position,
                y=self.y_mm,
                z=self.z_mm,
            )

        self._scintillator_out_yz_mm = [
            float(beamline_parameters[f"scin_{axis}_SCIN_OUT"]) for axis in ("y", "z")
        ]
        self._scintillator_in_yz_mm = [
            float(beamline_parameters[f"scin_{axis}_SCIN_IN"]) for axis in ("y", "z")
        ]
        self._yz_tolerance_mm = [
            float(beamline_parameters[f"scin_{axis}_tolerance"]) for axis in ("y", "z")
        ]

        super().__init__(name)

    def move_scintillator_safely(
        self,
        aperture_scatterguard: ApertureScatterguard,
        beamstop: Beamstop,
        position: InOut,
    ) -> MsgGenerator:
        """Bluesky plan to move the scintillator which moves the aperture-scatterguard out of the way
        for the duration of the move and then restores it.

        Args:
            aperture_scatterguard (ApertureScatterguard):
                The aperture-scatterguard device which will be moved
            beamstop (Beamstop):
                The beamstop device which will be checked for potential collisions
            position (InOut):
                The scintillator position to move to
        """
        current_pos = yield from bps.rd(self.selected_pos)
        if current_pos == position:
            return

        def _move_to_new_position():
            if position == InOut.OUT:
                yield from bps.mv(self.y_mm, self._scintillator_out_yz_mm[0])
                yield from bps.mv(self.z_mm, self._scintillator_out_yz_mm[1])
            elif position == InOut.IN:
                yield from bps.mv(self.z_mm, self._scintillator_in_yz_mm[1])
                yield from bps.mv(self.y_mm, self._scintillator_in_yz_mm[0])

        match position:
            case InOut.OUT | InOut.IN:
                yield from self._check_beamstop_position(beamstop)
                yield from do_with_aperture_scatterguard_in_scin_move_position(
                    aperture_scatterguard, _move_to_new_position
                )
            case _:
                raise ValueError(f"Cannot set scintillator to position {position}")

    def _check_position(self, current_pos: list[float], pos_to_check: list[float]):
        return all(
            isclose(axis_pos, axis_in_beam, abs_tol=axis_tolerance)
            for axis_pos, axis_in_beam, axis_tolerance in zip(
                current_pos,
                pos_to_check,
                self._yz_tolerance_mm,
                strict=False,
            )
        )

    def _get_selected_position(self, y: float, z: float) -> InOut:
        current_pos = [y, z]
        if self._check_position(current_pos, self._scintillator_out_yz_mm):
            return InOut.OUT

        elif self._check_position(current_pos, self._scintillator_in_yz_mm):
            return InOut.IN

        else:
            return InOut.UNKNOWN

    def _check_beamstop_position(self, beamstop: Beamstop) -> MsgGenerator:
        position = yield from bps.rd(beamstop.selected_pos)
        match position:
            case BeamstopPositions.OUT_OF_BEAM | BeamstopPositions.DATA_COLLECTION:
                return
            case _:
                raise ValueError(
                    f"Scintillator cannot be moved due to beamstop position {position}, must be in either in DATA_COLLECTION or OUT_OF_BEAM position."
                )
