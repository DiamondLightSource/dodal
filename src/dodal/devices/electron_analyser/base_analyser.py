from bluesky.protocols import Movable
from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_w


class BaseAnalyser(StandardReadable, Movable):
    """
    Generic device to configure electron analyser with new region settings.
    Electron analysers should inherit from this class if they need further
    specialisation.
    """

    PV_LENS_MODE = "LENS_MODE"
    PV_PASS_ENERGY = "PASS_ENERGY"
    PV_ACQISITION_MODE = "ACQ_MODE"
    PV_LOW_ENERGY = "LOW_ENERGY"
    PV_HIGH_ENERGY = "HIGH_ENERGY"
    PV_SLICES = "SLICES"
    PV_ITERATIONS = "NumExposures"
    PV_ENERGY_STEP = "STEP_SIZE"

    def __init__(self, prefix: str, name: str = "") -> None:
        self.prefix = prefix

        with self.add_children_as_readables():
            self.low_energy_signal = epics_signal_w(
                float, self.prefix + BaseAnalyser.PV_LOW_ENERGY
            )
            self.high_energy_signal = epics_signal_w(
                float, self.prefix + BaseAnalyser.PV_HIGH_ENERGY
            )

            self.slices_signal = epics_signal_w(
                int, self.prefix + BaseAnalyser.PV_SLICES
            )
            self.lens_mode_signal = epics_signal_w(
                str, self.prefix + BaseAnalyser.PV_LENS_MODE
            )
            self.pass_energy_signal = epics_signal_w(
                int, self.prefix + BaseAnalyser.PV_PASS_ENERGY
            )
            self.energy_step_signal = epics_signal_w(
                float, self.prefix + BaseAnalyser.PV_ENERGY_STEP
            )

            self.iterations_signal = epics_signal_w(
                int, self.prefix + BaseAnalyser.PV_ITERATIONS
            )

            self.acquisition_mode_signal = epics_signal_w(
                str, self.prefix + BaseAnalyser.PV_ACQISITION_MODE
            )

        super().__init__(name)
