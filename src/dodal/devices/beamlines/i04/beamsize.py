from ophyd_async.core import Reference, derived_signal_r

from dodal.devices.beamlines.i04.transfocator import Transfocator
from dodal.devices.beamsize.beamsize import BeamsizeBase
from dodal.devices.mx_phase1.aperturescatterguard import ApertureScatterguard


class Beamsize(BeamsizeBase):
    """Device that calculates the size of the beam by taking the minimum of the
    transfocator size and the aperture scatterguard diameter.
    """

    def __init__(
        self,
        transfocator: Transfocator,
        aperture_scatterguard: ApertureScatterguard,
        name="",
    ):
        super().__init__(name=name)
        self._transfocator_ref = Reference(transfocator)
        self._aperture_scatterguard_ref = Reference(aperture_scatterguard)

        with self.add_children_as_readables():
            self.x_um = derived_signal_r(
                self._get_beamsize_x,
                transfocator_size_x=self._transfocator_ref().current_horizontal_size_rbv,
                aperture_diameter=self._aperture_scatterguard_ref().diameter,
                derived_units="µm",
            )
            self.y_um = derived_signal_r(
                self._get_beamsize_y,
                transfocator_size_y=self._transfocator_ref().current_vertical_size_rbv,
                aperture_diameter=self._aperture_scatterguard_ref().diameter,
                derived_units="µm",
            )

    def _get_beamsize_x(
        self,
        transfocator_size_x: float,
        aperture_diameter: float,
    ) -> float:
        return min(transfocator_size_x, aperture_diameter)

    def _get_beamsize_y(
        self,
        transfocator_size_y: float,
        aperture_diameter: float,
    ) -> float:
        return min(transfocator_size_y, aperture_diameter)
