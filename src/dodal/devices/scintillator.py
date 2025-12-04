from math import isclose

from ophyd_async.core import Reference, StandardReadable, StrictEnum, derived_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.aperturescatterguard import ApertureScatterguard, ApertureValue


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

    async def _check_aperture_parked(self):
        if (
            await self._aperture_scatterguard().selected_aperture.get_value()
            != ApertureValue.PARKED
        ):
            raise ValueError(
                f"Cannot move scintillator if aperture/scatterguard is not parked. Position is currently {await self._aperture_scatterguard().selected_aperture.get_value()}"
            )

    async def _set_selected_position(self, position: InOut) -> None:
        match position:
            case InOut.OUT:
                current_y = await self.y_mm.user_readback.get_value()
                current_z = await self.z_mm.user_readback.get_value()
                if self._get_selected_position(current_y, current_z) == InOut.OUT:
                    return
                await self._check_aperture_parked()
                await self.y_mm.set(self._scintillator_out_yz_mm[0])
                await self.z_mm.set(self._scintillator_out_yz_mm[1])
            case InOut.IN:
                current_y = await self.y_mm.user_readback.get_value()
                current_z = await self.z_mm.user_readback.get_value()
                if self._get_selected_position(current_y, current_z) == InOut.IN:
                    return
                await self._check_aperture_parked()
                await self.z_mm.set(self._scintillator_in_yz_mm[1])
                await self.y_mm.set(self._scintillator_in_yz_mm[0])
            case _:
                raise ValueError(f"Cannot set scintillator to position {position}")
