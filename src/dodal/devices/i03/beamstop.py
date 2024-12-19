from asyncio import gather
from math import isclose

from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.common.signal_utils import create_hardware_backed_soft_signal


class BeamstopPositions(StrictEnum):
    """
    Beamstop positions.
    GDA supports Standard/High/Low resolution positions, as well as parked and
    robot load however all 3 resolution positions are the same. We also
    do not use the robot load position in Hyperion.

    Until we support moving the beamstop it is only necessary to check whether the
    beamstop is in beam or not.

    Attributes:
        IN_BEAM: The beamstop is in beam
        UNKNOWN: The beamstop is in some other position, check the device motor
            positions to determine it.
    """

    IN_BEAM = "In Beam"
    UNKNOWN = "Unknown"


class Beamstop(StandardReadable):
    """
    Beamstop for I03.

    Attributes:
        x: beamstop x position in mm
        y: beamstop y position in mm
        z: beamstop z position in mm
        pos_select: Get the current position of the beamstop as an enum. Currently this
            is read-only.
    """

    def __init__(
        self,
        prefix: str,
        beamline_parameters: GDABeamlineParameters,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + "X")
            self.y = Motor(prefix + "Y")
            self.z = Motor(prefix + "Z")
            self.pos_select = create_hardware_backed_soft_signal(
                BeamstopPositions, self._get_selected_position
            )

        self._in_beam_xyz = [
            float(beamline_parameters[f"in_beam_{axis}_STANDARD"])
            for axis in ("x", "y", "z")
        ]
        self._xyz_tolerance = [
            float(beamline_parameters[f"bs_{axis}_tolerance"])
            for axis in ("x", "y", "z")
        ]

        super().__init__(name)

    async def _get_selected_position(self) -> BeamstopPositions:
        current_pos = await gather(
            self.x.user_readback.get_value(),
            self.y.user_readback.get_value(),
            self.z.user_readback.get_value(),
        )
        if all(
            isclose(axis_pos, axis_in_beam, abs_tol=axis_tolerance)
            for axis_pos, axis_in_beam, axis_tolerance in zip(
                current_pos, self._in_beam_xyz, self._xyz_tolerance, strict=False
            )
        ):
            return BeamstopPositions.IN_BEAM
        else:
            return BeamstopPositions.UNKNOWN
