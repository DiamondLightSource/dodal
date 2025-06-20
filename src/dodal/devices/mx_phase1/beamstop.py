import asyncio
from math import isclose

from ophyd_async.core import (
    StrictEnum,
    derived_signal_rw,
)
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.motors import XYZStage


class BeamstopPositions(StrictEnum):
    """
    Beamstop positions.
    GDA supports Standard/High/Low resolution positions, as well as parked and
    robot load however all 3 resolution positions are the same. We also
    do not use the robot load position in Hyperion.

    Until we support moving the beamstop it is only necessary to check whether the
    beamstop is in beam or not.

    See Also:
        https://github.com/DiamondLightSource/mx-bluesky/issues/484

    Attributes:
        DATA_COLLECTION: The beamstop is in beam ready for data collection
        UNKNOWN: The beamstop is in some other position, check the device motor
            positions to determine it.
    """

    DATA_COLLECTION = "Data Collection"
    UNKNOWN = "Unknown"


class Beamstop(XYZStage):
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
            self.selected_pos = derived_signal_rw(
                self._get_selected_position,
                self._set_selected_position,
                x=self.x,
                y=self.y,
                z=self.z,
            )
        self._in_beam_xyz_mm = [
            float(beamline_parameters[f"in_beam_{axis}_STANDARD"])
            for axis in ("x", "y", "z")
        ]
        self._xyz_tolerance_mm = [
            float(beamline_parameters[f"bs_{axis}_tolerance"])
            for axis in ("x", "y", "z")
        ]

        super().__init__(prefix, name)

    @property
    def x_mm(self) -> Motor:
        return self.x

    @property
    def y_mm(self) -> Motor:
        return self.y

    @property
    def z_mm(self) -> Motor:
        return self.z

    def _get_selected_position(self, x: float, y: float, z: float) -> BeamstopPositions:
        current_pos = [x, y, z]
        if all(
            isclose(axis_pos, axis_in_beam, abs_tol=axis_tolerance)
            for axis_pos, axis_in_beam, axis_tolerance in zip(
                current_pos, self._in_beam_xyz_mm, self._xyz_tolerance_mm, strict=False
            )
        ):
            return BeamstopPositions.DATA_COLLECTION
        else:
            return BeamstopPositions.UNKNOWN

    async def _set_selected_position(self, position: BeamstopPositions) -> None:
        if position == BeamstopPositions.DATA_COLLECTION:
            await asyncio.gather(
                self.x.set(self._in_beam_xyz_mm[0]),
                self.y.set(self._in_beam_xyz_mm[1]),
                self.z.set(self._in_beam_xyz_mm[2]),
            )
        elif position == BeamstopPositions.UNKNOWN:
            raise ValueError(f"Cannot set beamstop to position {position}")
