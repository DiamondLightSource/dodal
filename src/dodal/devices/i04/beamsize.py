from ophyd_async.core import Reference, derived_signal_r

from dodal.devices.aperturescatterguard import ApertureScatterguard
from dodal.devices.beamsize.beamsize import BeamsizeBase
from dodal.devices.i04.transfocator import Transfocator


class Beamsize(BeamsizeBase):
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
                aperture_radius=self._aperture_scatterguard_ref().radius,
                derived_units="µm",
            )
            self.y_um = derived_signal_r(
                self._get_beamsize_y,
                transfocator_size_y=self._transfocator_ref().current_vertical_size_rbv,
                aperture_radius=self._aperture_scatterguard_ref().radius,
                derived_units="µm",
            )

    def _get_beamsize_x(
        self,
        transfocator_size_x: float,
        aperture_radius: float,
    ) -> float:
        return min(transfocator_size_x, aperture_radius)

    def _get_beamsize_y(
        self,
        transfocator_size_y: float,
        aperture_radius: float,
    ) -> float:
        return min(transfocator_size_y, aperture_radius)
