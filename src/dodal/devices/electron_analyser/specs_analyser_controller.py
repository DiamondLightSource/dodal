import numpy as np
from ophyd_async.core import Array1D
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.abstract_analyser_controller import (
    AbstractAnalyserController,
)
from dodal.devices.electron_analyser.abstract_region import EnergyMode
from dodal.devices.electron_analyser.util import to_binding_energy


class SpecsAnalyserController(AbstractAnalyserController):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            # Used for setting up region data acquisition
            self.psu_mode = epics_signal_rw(str, prefix + "SCAN_RANGE")
            self.values = epics_signal_rw(int, prefix + "VALUES")
            self.centre_energy = epics_signal_rw(float, prefix + "KINETIC_ENERGY")

            # Used to read detector data after acqusition
            self.min_angle_axis = epics_signal_r(float, prefix + "Y_MIN_RBV")
            self.max_angle_axis = epics_signal_r(float, prefix + "Y_MAX_RBV")
            self.total_points_iteration = epics_signal_r(
                float, prefix + "TOTAL_POINTS_ITERATIONS_RBV"
            )

        super().__init__(prefix, name)

    @property
    async def angle_axis(self) -> list[float]:
        min_angle = await self.min_angle_axis.get_value()
        max_angle = await self.max_angle_axis.get_value()
        slices = await self.slices.get_value()

        # SPECS returns the extreme edges of the range not the centre of the pixels
        width = (max_angle - min_angle) / slices
        offset = width / 2

        axis = [0.0] * slices
        for i in range(len(axis)):
            axis[i] = min_angle + offset + i * width
        return axis

    @property
    async def energy_axis(self) -> list[float]:
        min_energy = await self.low_energy.get_value()
        max_energy = await self.high_energy.get_value()
        total_points_iterations = await self.slices.get_value()

        step = (max_energy - min_energy) / total_points_iterations

        axis = [0.0] * total_points_iterations
        for i in range(len(axis)):
            axis[i] = min_energy + i * step
        return axis

    async def binding_energy_axis(
        self, excitation_energy: float
    ) -> Array1D[np.float64]:
        energy_axis_values = await self.energy_axis
        return np.array(
            to_binding_energy(energy_value, EnergyMode.KINETIC, excitation_energy)
            for energy_value in energy_axis_values
        )
