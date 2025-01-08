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

    See Also:
        https://github.com/DiamondLightSource/mx-bluesky/issues/484

    Attributes:
        DATA_COLLECTION: The beamstop is in beam ready for data collection
        UNKNOWN: The beamstop is in some other position, check the device motor
            positions to determine it.
    """

    DATA_COLLECTION = "Data Collection"
    UNKNOWN = "Unknown"


class Beamstop(StandardReadable):
    """
    Beamstop for I03.

    Attributes:
        x: beamstop x position in mm
        y: beamstop y position in mm
        z: beamstop z position in mm
        selected_pos: Get the current position of the beamstop as an enum. Currently this
            is read-only.
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
            self.selected_pos = create_hardware_backed_soft_signal(
                BeamstopPositions, self._get_selected_position
            )

        self._in_beam_xyz_mm = [
            float(beamline_parameters[f"in_beam_{axis}_STANDARD"])
            for axis in ("x", "y", "z")
        ]
        self._xyz_tolerance_mm = [
            float(beamline_parameters[f"bs_{axis}_tolerance"])
            for axis in ("x", "y", "z")
        ]

        super().__init__(name)

    async def _get_selected_position(self) -> BeamstopPositions:
        current_pos = await gather(
            self.x_mm.user_readback.get_value(),
            self.y_mm.user_readback.get_value(),
            self.z_mm.user_readback.get_value(),
        )
        if all(
            isclose(axis_pos, axis_in_beam, abs_tol=axis_tolerance)
            for axis_pos, axis_in_beam, axis_tolerance in zip(
                current_pos, self._in_beam_xyz_mm, self._xyz_tolerance_mm, strict=False
            )
        ):
            return BeamstopPositions.DATA_COLLECTION
        else:
            return BeamstopPositions.UNKNOWN
