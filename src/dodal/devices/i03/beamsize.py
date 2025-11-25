from ophyd_async.core import Reference, derived_signal_r

from dodal.devices.aperturescatterguard import ApertureScatterguard
from dodal.devices.beamsize.beamsize import BeamsizeBase
from dodal.devices.i03.constants import BeamsizeConstants


class Beamsize(BeamsizeBase):
    def __init__(self, aperture_scatterguard: ApertureScatterguard, name=""):
        super().__init__(name=name)
        self._aperture_scatterguard_ref = Reference(aperture_scatterguard)

        with self.add_children_as_readables():
            self.x_um = derived_signal_r(
                self._get_beamsize_x,
                aperture_radius=self._aperture_scatterguard_ref().radius,
                derived_units="µm",
            )
            self.y_um = derived_signal_r(
                self._get_beamsize_y,
                aperture_radius=self._aperture_scatterguard_ref().radius,
                derived_units="µm",
            )

    def _get_beamsize_x(
        self,
        aperture_radius: float,
    ) -> float:
        return min(aperture_radius, BeamsizeConstants.BEAM_WIDTH_UM)

    def _get_beamsize_y(
        self,
        aperture_radius: float,
    ) -> float:
        return min(aperture_radius, BeamsizeConstants.BEAM_HEIGHT_UM)
