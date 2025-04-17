import numpy as np
from ophyd_async.core import Array1D, SignalR
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.signal_utils import create_r_hardware_backed_soft_signal
from dodal.devices.electron_analyser.abstract_analyser_io import (
    AbstractAnalyserDriverIO,
)


class SpecsAnalyserDriverIO(AbstractAnalyserDriverIO):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            # Used for setting up region data acquisition. Per scan.
            self.psu_mode = epics_signal_rw(str, prefix + "SCAN_RANGE")
            self.values = epics_signal_rw(int, prefix + "VALUES")
            self.centre_energy = epics_signal_rw(float, prefix + "KINETIC_ENERGY")

            # Used to read detector data after acqusition. Per scan.
            self.min_angle_axis = epics_signal_r(float, prefix + "Y_MIN_RBV")
            self.max_angle_axis = epics_signal_r(float, prefix + "Y_MAX_RBV")

        super().__init__(prefix, name)

    def _get_angle_axis_signal(self, prefix: str = "") -> SignalR:
        """
        Override abstract and return soft signal that calculates angle axis
        """
        if hasattr(self, "angle_axis"):
            return self.angle_axis
        angle_axis = create_r_hardware_backed_soft_signal(
            Array1D[np.float64], self._calculate_angle_axis, units="eV"
        )
        return angle_axis

    async def _calculate_angle_axis(self) -> Array1D[np.float64]:
        min_angle = await self.min_angle_axis.get_value()
        max_angle = await self.max_angle_axis.get_value()
        slices = await self.slices.get_value()

        # SPECS returns the extreme edges of the range, not the centre of the pixels
        width = (max_angle - min_angle) / slices
        offset = width / 2

        axis = np.array([min_angle + offset + i * width for i in range(slices)])
        return axis

    def _get_energy_axis_signal(self, prefix: str = "") -> SignalR:
        """
        Override abstract and return soft signal that calculates energy axis
        """
        if hasattr(self, "energy_axis"):
            return self.energy_axis
        energy_axis = create_r_hardware_backed_soft_signal(
            Array1D[np.float64], self._calculate_energy_axis, units="eV"
        )
        return energy_axis

    async def _calculate_energy_axis(self) -> Array1D[np.float64]:
        min_energy = await self.low_energy.get_value()
        max_energy = await self.high_energy.get_value()
        total_points_iterations = await self.slices.get_value()

        step = (max_energy - min_energy) / total_points_iterations
        axis = np.array([min_energy + i * step for i in range(total_points_iterations)])
        return axis

    @property
    def pass_energy_type(self) -> type:
        return float
