from math import isclose

import bluesky.plan_stubs as bps
from bluesky.utils import MsgGenerator
from ophyd_async.core import Reference, StandardReadable, StrictEnum, derived_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.mx_phase1.aperturescatterguard import (
    ApertureScatterguard,
    ApertureValue,
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
        aperture_scatterguard: Reference[ApertureScatterguard],
        beamstop: Reference[Beamstop],
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.y_mm = Motor(f"{prefix}Y")
            self.z_mm = Motor(f"{prefix}Z")
            self.selected_pos = derived_signal_rw(
                self._get_selected_position,
                self._set_selected_position,
                y=self.y_mm,
                z=self.z_mm,
            )
        self._beamstop = beamstop
        self._aperture_scatterguard = aperture_scatterguard

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
            yield from bps.abs_set(self.selected_pos, position, wait=True)

        match position:
            case InOut.OUT | InOut.IN:
                yield from do_with_aperture_scatterguard_in_scin_move_position(
                    self._aperture_scatterguard(), _move_to_new_position
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

    async def _set_selected_position(self, position: InOut) -> None:
        current_y = await self.y_mm.user_readback.get_value()
        current_z = await self.z_mm.user_readback.get_value()
        if self._get_selected_position(current_y, current_z) == position:
            return

        await self._check_beamstop_position()
        aperture_scatterguard_pos = (
            await self._aperture_scatterguard().selected_aperture.get_value()
        )
        if aperture_scatterguard_pos != ApertureValue.SCIN_MOVE:
            raise ValueError(
                "Scintillator cannot be moved while aperture-scatterguard not in SCIN_MOVE position"
            )

        match position:
            case InOut.OUT | InOut.IN:
                await self._move_to_new_position(position)
            case _:
                raise ValueError(f"Cannot set scintillator to position {position}")

    async def _move_to_new_position(self, position):
        if position == InOut.OUT:
            await self.y_mm.set(self._scintillator_out_yz_mm[0])
            await self.z_mm.set(self._scintillator_out_yz_mm[1])
        elif position == InOut.IN:
            await self.z_mm.set(self._scintillator_in_yz_mm[1])
            await self.y_mm.set(self._scintillator_in_yz_mm[0])

    async def _check_beamstop_position(self):
        position = await self._beamstop().selected_pos.get_value()
        match position:
            case BeamstopPositions.OUT_OF_BEAM | BeamstopPositions.DATA_COLLECTION:
                return
            case _:
                raise ValueError(
                    f"Scintillator cannot be moved due to beamstop position {position}, must be in either in DATA_COLLECTION or OUT_OF_BEAM position."
                )
