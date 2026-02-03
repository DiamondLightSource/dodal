from functools import partial
from math import isclose

from ophyd_async.core import Reference, StandardReadable, StrictEnum, derived_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.aperturescatterguard import ApertureScatterguard
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
    """

    def __init__(
        self,
        prefix: str,
        aperture_scatterguard: Reference[ApertureScatterguard],
        beamstop: Reference[Beamstop],
        beamline_parameters: GDABeamlineParameters,
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

        self._aperture_scatterguard = aperture_scatterguard
        self._beamstop = beamstop
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

    async def _check_beamstop_position(self):
        position = await self._beamstop().selected_pos.get_value()
        match position:
            case BeamstopPositions.OUT_OF_BEAM | BeamstopPositions.DATA_COLLECTION:
                return
            case _:
                raise ValueError(
                    f"Scintillator cannot be moved due to beamstop position {position}, must be in either in DATA_COLLECTION or OUT_OF_BEAM position."
                )

    async def _set_selected_position(self, position: InOut) -> None:
        current_y = await self.y_mm.user_readback.get_value()
        current_z = await self.z_mm.user_readback.get_value()
        if self._get_selected_position(current_y, current_z) == position:
            return

        await self._check_beamstop_position()

        match position:
            case InOut.OUT | InOut.IN:
                await self.do_with_aperture_scatterguard_in_safe_pos(
                    partial(self._move_to_new_position, position)
                )
            case _:
                raise ValueError(f"Cannot set scintillator to position {position}")

    async def _move_to_new_position(self, position):
        if position == InOut.OUT:
            await self.y_mm.set(self._scintillator_out_yz_mm[0])
            await self.z_mm.set(self._scintillator_out_yz_mm[1])
        elif position == InOut.IN:
            await self.z_mm.set(self._scintillator_in_yz_mm[1])
            await self.y_mm.set(self._scintillator_in_yz_mm[0])

    async def do_with_aperture_scatterguard_in_safe_pos(self, func):
        """Move the aperture-scatterguard to SCIN_MOVE position, do the supplied function,
        then restore aperture-scatterguard  to its previous position.
        Args:
            func: The async function to be applied"""
        scin_move_positions = self._aperture_scatterguard().get_scin_move_position()
        saved_positions: dict[Motor, float] = {
            motor: await motor.user_readback.get_value()
            for motor in scin_move_positions
        }
        for motor, pos in scin_move_positions.items():
            await motor.set(pos)

        await func()
        # If  func() fails then do not restore motors back to avoid potential collision
        for motor, pos in saved_positions.items():
            await motor.set(pos)
