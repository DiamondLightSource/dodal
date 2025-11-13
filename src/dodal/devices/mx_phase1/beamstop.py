import asyncio
from math import isclose

from ophyd_async.core import (
    StandardReadable,
    StrictEnum,
    derived_signal_rw,
)
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters

_BEAMSTOP_OUT_DELTA_Y_MM = -2


class BeamstopPositions(StrictEnum):
    """
    Beamstop positions.
    GDA supports Standard/High/Low resolution positions, as well as parked and
    robot load however all 3 resolution positions are the same. We also
    do not use the robot load position in Hyperion.

    See Also:
        https://github.com/DiamondLightSource/mx-bluesky/issues/484

    Attributes:
        DATA_COLLECTION: The beamstop is in beam ready for data collection
        UNKNOWN: The beamstop is in some other position, check the device motor
            positions to determine it.
    """

    DATA_COLLECTION = "Data Collection"
    OUT_OF_BEAM = "Out"
    UNKNOWN = "Unknown"


class Beamstop(StandardReadable):
    """
    Beamstop for I03 and I04.

    Attributes:
        x: beamstop x position in mm
        y: beamstop y position in mm
        z: beamstop z position in mm
        selected_pos: Get or set the current position of the beamstop as an enum.
    """

    def __init__(
        self,
        prefix: str,
        beamline_parameters: GDABeamlineParameters,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.x_mm = Motor(prefix + "X")
            self.y_mm = Motor(prefix + "Y")
            self.z_mm = Motor(prefix + "Z")
            self.selected_pos = derived_signal_rw(
                self._get_selected_position,
                self._set_selected_position,
                x=self.x_mm,
                y=self.y_mm,
                z=self.z_mm,
            )
        self._in_beam_xyz_mm = [
            float(beamline_parameters[f"in_beam_{axis}_STANDARD"])
            for axis in ("x", "y", "z")
        ]

        self._out_of_beam_xyz_mm = list(self._in_beam_xyz_mm)
        self._out_of_beam_xyz_mm[1] += _BEAMSTOP_OUT_DELTA_Y_MM

        self._xyz_tolerance_mm = [
            float(beamline_parameters[f"bs_{axis}_tolerance"])
            for axis in ("x", "y", "z")
        ]

        super().__init__(name)

    def _get_selected_position(self, x: float, y: float, z: float) -> BeamstopPositions:
        current_pos = [x, y, z]
        if self._is_near_position(current_pos, self._in_beam_xyz_mm):
            return BeamstopPositions.DATA_COLLECTION
        elif self._is_near_position(current_pos, self._out_of_beam_xyz_mm):
            return BeamstopPositions.OUT_OF_BEAM
        else:
            return BeamstopPositions.UNKNOWN

    def _is_near_position(
        self, current_pos: list[float], target_pos: list[float]
    ) -> bool:
        return all(
            isclose(axis_pos, axis_in_beam, abs_tol=axis_tolerance)
            for axis_pos, axis_in_beam, axis_tolerance in zip(
                current_pos, target_pos, self._xyz_tolerance_mm, strict=False
            )
        )

    async def _set_selected_position(self, position: BeamstopPositions) -> None:
        match position:
            case BeamstopPositions.DATA_COLLECTION:
                await self._safe_move_above_table(self._in_beam_xyz_mm)
            case BeamstopPositions.OUT_OF_BEAM:
                await self._safe_move_above_table(self._out_of_beam_xyz_mm)
            case _:
                raise ValueError(f"Cannot set beamstop to position {position}")

    async def _safe_move_above_table(self, pos: list[float]):
        # Move z first as it could be under the table
        await self.z_mm.set(pos[2])
        await asyncio.gather(
            self.x_mm.set(pos[0]),
            self.y_mm.set(pos[1]),
        )
